import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder import BatchEmbedderResource


@asset(
    partitions_def=user_partitions_def,
    ins={
        "deduplicated_graph": AssetIn(
            key=["deduplicated_graph"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def deduplicated_graph_w_embeddings(
    context: AssetExecutionContext,
    batch_embedder: BatchEmbedderResource,
    deduplicated_graph: pl.DataFrame,
) -> pl.DataFrame:
    logger = context.log

    # Get descriptions and labels
    nodes_to_process = deduplicated_graph.filter(pl.col("frequency") > 1)
    logger.info(f"Processing {len(nodes_to_process)} nodes for embedding...")

    # Get embeddings for all descriptions in one batch
    total_cost, embeddings = await batch_embedder.get_embeddings(
        nodes_to_process.get_column("description").to_list()
    )

    logger.info(
        f"Generated embeddings for {len(nodes_to_process)} nodes. Cost: ${total_cost:.2f}"
    )

    # Create a new DataFrame with just labels and embeddings
    embedding_df = pl.DataFrame(
        {"label": nodes_to_process.get_column("label"), "new_embedding": embeddings}
    )

    # Join the embeddings back to the original DataFrame
    result = (
        deduplicated_graph.join(embedding_df, on="label", how="left")
        .with_columns(
            [pl.col("new_embedding").fill_null(pl.col("embedding")).alias("embedding")]
        )
        .drop("new_embedding")
    )

    return result
