import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource


def _get_exploded_df(
    df: pl.DataFrame,
    claim_type: str,
) -> pl.DataFrame:
    col_to_explode = f"subgraph_{claim_type}"

    res_df = (
        df.select("chunk_id", col_to_explode)
        .explode(col_to_explode)
        .with_columns(
            pl.col(col_to_explode).struct.unnest(),
        )
        .drop(col_to_explode)
        .filter(pl.col("proposition").is_not_null())
        .cast(
            {
                "id": pl.Utf8,
                "datetime": pl.Utf8,
                "proposition": pl.Utf8,
                "caused_by": pl.List(pl.Utf8),
                "caused": pl.List(pl.Utf8),
            }
        )
    )

    return res_df


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_cross_chunk_causality": AssetIn(
            key=["whatsapp_cross_chunk_causality"],
        ),
    },
)
async def whatsapp_node_embeddings(
    context: AssetExecutionContext,
    config: Config,
    whatsapp_cross_chunk_causality: pl.DataFrame,
    batch_embedder: BatchEmbedderResource,
) -> pl.DataFrame:
    # df = pl.concat(
    #     [
    #         _get_exploded_df(whatsapp_cross_chunk_causality, "meta"),
    #         _get_exploded_df(whatsapp_cross_chunk_causality, "context"),
    #         _get_exploded_df(whatsapp_cross_chunk_causality, "attributes"),
    #     ],
    #     how="vertical",
    # )

    df = _get_exploded_df(whatsapp_cross_chunk_causality, "combined")

    cost, embeddings = await batch_embedder.get_embeddings(
        df.get_column("proposition").to_list(),
        api_batch_size=32,
        gpu_batch_size=32,
    )

    context.log.info(f"Total cost: ${cost:.2f}")

    return df.with_columns(pl.Series(embeddings).alias("embedding"))
