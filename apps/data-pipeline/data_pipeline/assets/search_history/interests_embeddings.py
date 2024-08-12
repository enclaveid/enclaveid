import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.resources.llm_inference.sentence_transformer_resource import (
    SentenceTransformerResource,
)

from ...constants.k8s import k8s_vllm_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info


class InterestsEmbeddingsConfig(RowLimitConfig):
    ml_model_name: str = Field(
        default="Salesforce/SFR-Embedding-2_R",
        description=("The Hugging Face model to use with SentenceTransformers."),
    )

    chunk_size: int = Field(
        default=15,
        description=(
            "Split the raw history into chunks of this size. We allow vLLM to "
            "determine the ideal batch size by itsef, so this has no impact on "
            "runtime but it still determines how many records are shown to the "
            "LLM at one time. Having too many records can cause the LLM to give "
            "sub-par responses."
        ),
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={"interests": AssetIn(key=["interests"])},
    op_tags=k8s_vllm_config,
)
def interests_embeddings(
    context: AssetExecutionContext,
    config: InterestsEmbeddingsConfig,
    sentence_transformer: SentenceTransformerResource,
    interests: pl.DataFrame,
) -> pl.DataFrame:
    context.log.info(gpu_info())

    df = (
        # Enforce row_limit (if any)
        interests.slice(0, config.row_limit)
        .select("date", "interests")
        # Explode the interests so we get the embeddings for each individual interest
        .explode("interests")
        .drop_nulls()
    )

    context.log.info("Computing embeddings")
    return df.with_columns(
        embeddings=pl.col("interests").map_batches(sentence_transformer.get_embeddings)
    )
