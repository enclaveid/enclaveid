import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.utils.pca.reduce_df_embeddings import reduce_df_embeddings
from data_pipeline.utils.pca.save_reducer import save_reducer


@asset(
    ins={
        "whatsapp_chunk_embeddings": AssetIn(
            key="whatsapp_chunk_embeddings",
        ),
    },
    io_manager_key="parquet_io_manager",
    partitions_def=multi_phone_number_partitions_def,
)
def whatsapp_out_chunks(
    context: AssetExecutionContext,
    whatsapp_chunk_embeddings: pl.DataFrame,
):
    context.log.info("Running PCA...")

    df, reducer = reduce_df_embeddings(whatsapp_chunk_embeddings)

    context.log.info("Saving reducer...")

    save_reducer(reducer, context)

    return df
