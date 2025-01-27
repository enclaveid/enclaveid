import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_embedder import BatchEmbedderResource

# We'll exclude these columns because of explosion
CHUNK_COLS = [
    "start_dt",
    "end_dt",
    "decisions",
    "messages_struct",
    "messages_str",
    "raw_analysis",
]


def _get_exploded_df(
    df: pl.DataFrame, claim_type: str, claim_subject: str
) -> pl.DataFrame:
    claim_counterpart = "partner" if claim_subject == "me" else "me"
    col_to_explode = f"{claim_type}s_{claim_subject}"
    col_to_explode_is_struct = df.schema[col_to_explode] != pl.List(pl.String)

    if col_to_explode_is_struct:
        claim_text_expr = pl.col(col_to_explode).struct.field("claim")
        claim_datetime_expr = (
            pl.col(col_to_explode)
            .struct.field("datetime")
            .str.to_datetime(strict=False)
        )
    else:
        claim_text_expr = pl.col(col_to_explode)
        claim_datetime_expr = pl.lit(None, dtype=pl.Datetime)

    return (
        df.select(pl.exclude(*CHUNK_COLS, f"{claim_type}s_{claim_counterpart}"))
        .explode(col_to_explode)
        .with_columns(
            [
                claim_text_expr.alias("claim_text"),
                claim_datetime_expr.alias("claim_datetime"),
                pl.lit(claim_type).alias("claim_type"),
                pl.lit(claim_subject).alias("claim_subject"),
            ]
        )
        .drop(col_to_explode)
        .filter(pl.col("claim_text").is_not_null())
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_chunks_subgraphs": AssetIn(
            key=["whatsapp_chunks_subgraphs"],
        ),
    },
)
async def whatsapp_claims_embeddings(
    context: AssetExecutionContext,
    config: Config,
    whatsapp_chunks_subgraphs: pl.DataFrame,
    batch_embedder: BatchEmbedderResource,
) -> pl.DataFrame:
    df = pl.concat(
        [
            _get_exploded_df(whatsapp_chunks_observables, "observable", "me"),
            _get_exploded_df(whatsapp_chunks_observables, "observable", "partner"),
            _get_exploded_df(whatsapp_chunks_inferrables, "inferrable", "me"),
            _get_exploded_df(whatsapp_chunks_inferrables, "inferrable", "partner"),
            _get_exploded_df(whatsapp_chunks_speculatives, "speculative", "me"),
            _get_exploded_df(whatsapp_chunks_speculatives, "speculative", "partner"),
        ],
        how="vertical",
    )

    cost, embeddings = await batch_embedder.get_embeddings(
        df.get_column("claim_text").to_list(),
        api_batch_size=32,
        gpu_batch_size=32,
    )

    context.log.info(f"Total cost: ${cost:.2f}")

    return df.with_columns(pl.Series(embeddings).alias("embedding"))
