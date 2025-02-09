import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.utils.pca.reduce_df_embeddings import reduce_df_embeddings
from data_pipeline.utils.pca.save_reducer import save_reducer


@asset(
    ins={
        "whatsapp_node_sentiments": AssetIn(
            key="whatsapp_node_sentiments",
        ),
    },
    io_manager_key="parquet_io_manager",
    partitions_def=multi_phone_number_partitions_def,
)
def whatsapp_out_nodes(
    context: AssetExecutionContext,
    whatsapp_node_sentiments: pl.DataFrame,
):
    context.log.info("Running PCA...")

    df, reducer = reduce_df_embeddings(whatsapp_node_sentiments)

    context.log.info("Saving reducer...")

    save_reducer(reducer, context)

    return df
