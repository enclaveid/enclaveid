import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.embeddings.nvembed_resource import NVEmbedResource


@asset(
    io_manager_key="parquet_io_manager",
    partitions_def=user_partitions_def,
    ins={
        "conversation_summaries": AssetIn(key=["conversation_summaries"]),
    },
    op_tags=get_k8s_vllm_config(),
)
def conversation_embeddings(
    context: AssetExecutionContext,
    conversation_summaries: pl.DataFrame,
    nvembed: NVEmbedResource,
) -> pl.DataFrame:
    embeddings, cost = nvembed.get_embeddings(conversation_summaries["summary"])
    context.log.info(f"Estimated cost: ${cost:.2f}")
    return conversation_summaries.with_columns(summary_embedding=embeddings)
