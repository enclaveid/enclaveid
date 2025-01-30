import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource


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
    df = speculatives_query_entities

    cost, embeddings = await batch_embedder.get_embeddings(
        df.get_column("seed_nodes").to_list(),
        api_batch_size=32,
        gpu_batch_size=32,
    )

    context.log.info(f"Embeddings cost: ${cost:.2f}")

    return df.with_columns(pl.Series(embeddings).alias("embedding"))
