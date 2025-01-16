import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder import BatchEmbedderResource


class NodeEmbeddingsConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    ins={
        "graph_nodes": AssetIn(
            key=["graph_nodes"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def node_embeddings(
    context: AssetExecutionContext,
    config: NodeEmbeddingsConfig,
    batch_embedder: BatchEmbedderResource,
    graph_nodes: pl.DataFrame,
) -> pl.DataFrame:
    embedder = batch_embedder
    df = graph_nodes.slice(0, config.row_limit)

    cost, embeddings = await embedder.get_embeddings(
        df["description"].to_list(),
        gpu_batch_size=3,  # The descriptions are small so we can fit 3 in a GPU batch
        api_batch_size=3,
    )
    context.log.info(f"Total embedding cost: ${cost:.2f}")

    # Add embedding columns to the result DataFrame
    result = df.with_columns(
        embedding=pl.Series(
            dtype=pl.List(pl.Float64),
            name="embedding",
            values=embeddings,
            strict=False,
        )
    )

    # Check for invalid embeddings
    invalid_embeddings = result.filter(pl.col("embedding").is_null())

    if invalid_embeddings.height > 0:
        context.log.warning(f"Found {invalid_embeddings.height} invalid embeddings.")

    # Filter out rows with invalid embeddings
    result = result.join(invalid_embeddings, on="label", how="anti")

    return result.filter(pl.col("embedding").is_not_null())
