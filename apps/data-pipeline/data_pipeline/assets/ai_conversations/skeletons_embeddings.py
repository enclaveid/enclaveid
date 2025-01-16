import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder import BatchEmbedderResource


class ConversationEmbeddingsConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    ins={
        "conversation_skeletons": AssetIn(
            key=["conversation_skeletons"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def skeletons_embeddings(
    context: AssetExecutionContext,
    config: ConversationEmbeddingsConfig,
    batch_embedder: BatchEmbedderResource,
    conversation_skeletons: pl.DataFrame,
) -> pl.DataFrame:
    """
    Creates embeddings for combined questions and answers in the parsed conversations.

    Args:
        context: The asset execution context
        config: Configuration for row limiting
        batch_embedder: Resource for creating embeddings
        parsed_conversations: DataFrame containing the parsed conversations

    Returns:
        DataFrame with added embedding column for combined question and answer text
    """
    embedder = batch_embedder
    df = conversation_skeletons.slice(0, config.row_limit)

    # Combine questions and answers
    combined_texts = (
        df.select(
            pl.col("skeleton").map_elements(
                lambda x: "\n".join(
                    [f"Q: {y['question']}\nA: {y['answer']}" for y in x]
                )
            )
        )
        .to_series()
        .to_list()
    )

    # Get embeddings for combined texts
    cost, embeddings = await embedder.get_embeddings(combined_texts)
    context.log.info(f"Embedding cost: ${cost:.2f}")

    # Add embedding column to the result DataFrame
    result = df.with_columns(
        [
            pl.Series(
                dtype=pl.List(pl.Float64),
                name="embedding",
                values=embeddings,
                strict=False,
            ),
        ]
    )

    # Check for invalid embeddings
    invalid_embeddings = result.filter(pl.col("embedding").is_null())

    if invalid_embeddings.height > 0:
        context.log.warning(f"Found {invalid_embeddings.height} invalid embeddings.")

    # Filter out rows with invalid embeddings
    result = result.filter(pl.col("embedding").is_not_null())

    return result
