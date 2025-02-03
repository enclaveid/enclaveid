import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.postgres_resource import PostgresResource
from data_pipeline.utils.get_messaging_partners import get_messaging_partners
from data_pipeline.utils.graph.build_graph_from_df import build_graph_from_df
from data_pipeline.utils.graph.save_graph import save_graph
from data_pipeline.utils.super_deduplicator import deduplicate_nodes_dataframe


class WhatsappClaimsDeduplicatedConfig(Config):
    threshold: float = Field(
        default=0.9, description="Cosine similarity threshold for merging claims"
    )
    debug_graph: bool = Field(
        default=True, description="Whether to save the graph to the debug directory"
    )


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_node_embeddings": AssetIn(
            key=["whatsapp_node_embeddings"],
        ),
    },
)
async def whatsapp_nodes_deduplicated(
    context: AssetExecutionContext,
    config: WhatsappClaimsDeduplicatedConfig,
    whatsapp_node_embeddings: pl.DataFrame,
    postgres: PostgresResource,
) -> pl.DataFrame:
    messaging_partners = get_messaging_partners(
        postgres, context.partition_keys[0].split("|")
    )

    # Gather embeddings and find similarities
    df = whatsapp_node_embeddings

    # Add a user column based on the contents of the proposition column
    df = df.with_columns(
        pl.when(
            # Check if both names appear in either order using regex
            pl.col("proposition").str.contains(
                f"{messaging_partners.initiator_name} and {messaging_partners.partner_name}|{messaging_partners.partner_name} and {messaging_partners.initiator_name}"
            )
        )
        .then(pl.lit("both"))
        # Check which name appears first and use that
        .when(
            pl.col("proposition")
            .str.extract(
                f"({messaging_partners.initiator_name}|{messaging_partners.partner_name})",
                0,
            )
            .is_not_null()
        )
        .then(
            pl.col("proposition").str.extract(
                f"({messaging_partners.initiator_name}|{messaging_partners.partner_name})",
                0,
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
                df.filter(pl.col("user") == messaging_partners.initiator_name),
                **deduplication_args,
            ),
            deduplicate_nodes_dataframe(
                df.filter(pl.col("user") == messaging_partners.partner_name),
                **deduplication_args,
            ),
        ],
        how="vertical",
    )

    if config.debug_graph:
        save_graph(
            build_graph_from_df(
                deduplicated_df,
                "relationships",
                "id",
                ["frequency", "user", "proposition", "chunk_id"],
            ),
            context,
        )

    return deduplicated_df
