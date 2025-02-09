import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_chunks_subgraphs": AssetIn(
            key=["whatsapp_chunks_subgraphs"],
        ),
    },
)
async def whatsapp_chunk_embeddings(
    context: AssetExecutionContext,
    whatsapp_chunks_subgraphs: pl.DataFrame,
    batch_embedder: BatchEmbedderResource,
) -> pl.DataFrame:
    cost, embeddings = await batch_embedder.get_embeddings(
        whatsapp_chunks_subgraphs.get_column("messages_str").to_list(),
        api_batch_size=10,
    )

    context.log.info(f"Total cost: ${cost:.2f}")

    return whatsapp_chunks_subgraphs.with_columns(
        pl.Series(embeddings).alias("embedding"),
    )
