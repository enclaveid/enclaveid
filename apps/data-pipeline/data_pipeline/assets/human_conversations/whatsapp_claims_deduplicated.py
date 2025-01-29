import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.get_messaging_partners import get_messaging_partners
from data_pipeline.utils.graph.build_graph_from_df import build_graph_from_df
from data_pipeline.utils.graph.save_graph import save_graph
from data_pipeline.utils.super_deduplicator import deduplicate_nodes_dataframe


class WhatsappClaimsDeduplicatedConfig(Config):
    threshold: float = Field(
        default=0.9, description="Cosine similarity threshold for merging claims"
    )


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_claims_embeddings": AssetIn(
            key=["whatsapp_claims_embeddings"],
        ),
    },
)
async def whatsapp_claims_deduplicated(
    context: AssetExecutionContext,
    config: WhatsappClaimsDeduplicatedConfig,
    whatsapp_claims_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    messaging_partners = get_messaging_partners()

    # Gather embeddings and find similarities
    df = whatsapp_claims_embeddings

    # Add a user column based on the contents of the proposition column
    df = df.with_columns(
        pl.when(
            # Check if both names appear in either order using regex
            pl.col("proposition").str.contains(
                f"{messaging_partners.me} and {messaging_partners.partner}|{messaging_partners.partner} and {messaging_partners.me}"
            )
        )
        .then(pl.lit("both"))
        # Check which name appears first and use that
        .when(
            pl.col("proposition")
            .str.extract(f"({messaging_partners.me}|{messaging_partners.partner})", 0)
            .is_not_null()
        )
        .then(
            pl.col("proposition").str.extract(
                f"({messaging_partners.me}|{messaging_partners.partner})", 0
            )
        )
        .otherwise(pl.lit("both"))
        .alias("user")
    )

    # Create a relationship column
    df = df.with_columns(
        pl.when(
            (pl.col("caused").list.len() > 0) | (pl.col("caused_by").list.len() > 0)
        )
        .then(
            # Build a new list of relationship dicts for each row
            pl.struct(["id", "caused", "caused_by"]).map_elements(
                lambda row: (
                    # Relationships from this node -> items in caused
                    [{"source": row["id"], "target": c} for c in row["caused"]]
                    +
                    # Relationships from items in caused_by -> this node
                    [{"source": c_by, "target": row["id"]} for c_by in row["caused_by"]]
                ),
                return_dtype=pl.List(
                    pl.Struct(
                        [pl.Field("source", pl.Utf8), pl.Field("target", pl.Utf8)]
                    )
                ),
            )
        )
        .otherwise(None)
        .alias("relationships")
    )

    deduplication_args = {
        "label_col": "id",
        "embedding_col": "embedding",
        "single_fields": ["proposition", "embedding", "user", "chunk_id"],
        "list_fields": [
            ("ids", "id"),
            ("chunk_ids", "chunk_id"),
            ("datetimes", "datetime"),
            # ("propositions", "proposition"),
            # ("embeddings", "embedding"),
        ],
        "relationship_col": "relationships",
        "threshold": config.threshold,
    }

    # Deduplicate within user groups
    deduplicated_df = pl.concat(
        [
            deduplicate_nodes_dataframe(
                df.filter(pl.col("user") == "both"), **deduplication_args
            ),
            deduplicate_nodes_dataframe(
                df.filter(pl.col("user") == messaging_partners.me), **deduplication_args
            ),
            deduplicate_nodes_dataframe(
                df.filter(pl.col("user") == messaging_partners.partner),
                **deduplication_args,
            ),
        ],
        how="vertical",
    )

    G = build_graph_from_df(
        deduplicated_df,
        "relationships",
        "id",
        ["frequency", "user", "proposition", "chunk_id"],
    )
    save_graph(G, context)

    return deduplicated_df
