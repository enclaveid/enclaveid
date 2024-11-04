import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.consts import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.nvembed_resource import NVEmbedResource

TEST_CONVERSATIONS_LIMIT = 10 if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "parsed_conversations": AssetIn(
            key=["parsed_conversations"],
        ),
    },
    op_tags=get_k8s_vllm_config(),
)
def conversations_embeddings(
    context: AssetExecutionContext,
    parsed_conversations: pl.DataFrame,
    nvembed: NVEmbedResource,
) -> pl.DataFrame:
    df = (
        parsed_conversations.with_columns(
            pl.concat_str(
                [
                    pl.col("date"),
                    pl.lit(" at "),
                    pl.col("time"),
                    pl.lit("----------------------------------------"),
                    pl.lit("\n QUESTION: "),
                    pl.col("question"),
                    pl.lit("\n ANSWER: "),
                    pl.col("answer"),
                ],
            ).alias("conversation_text")
        )
        .group_by("conversation_id")
        .agg(
            [
                pl.col("question").str.concat("\n").alias("question"),
                pl.col("conversation_text").str.concat("\n").alias("conversation_text"),
            ]
        )
        .slice(0, TEST_CONVERSATIONS_LIMIT)
    )

    question_embeddings = nvembed.get_embeddings(df["question"])
    conversation_embeddings = nvembed.get_embeddings(df["conversation_text"])

    # context.log.info(f"Estimated cost: ${cost:.2f}")

    return df.with_columns(
        question_embeddings=question_embeddings,
        conversation_embeddings=conversation_embeddings,
    )
