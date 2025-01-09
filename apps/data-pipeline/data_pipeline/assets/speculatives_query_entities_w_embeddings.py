import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder import BatchEmbedderResource


@asset(
    partitions_def=user_partitions_def,
    ins={
        "speculatives_query_entities": AssetIn(
            key=["speculatives_query_entities"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
async def speculatives_query_entities_w_embeddings(
    context: AssetExecutionContext,
    speculatives_query_entities: pl.DataFrame,
    batch_embedder: BatchEmbedderResource,
) -> pl.DataFrame:
    embeddings = await batch_embedder.get_embeddings(
        speculatives_query_entities.get_column("seed_nodes").to_list()
    )

    return speculatives_query_entities.with_columns(
        pl.Series(embeddings).alias("embedding")
    )
