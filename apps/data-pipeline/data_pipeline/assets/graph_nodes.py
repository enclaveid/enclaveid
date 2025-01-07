import networkx as nx
import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.constants.environments import DAGSTER_STORAGE_DIRECTORY
from data_pipeline.partitions import user_partitions_def


class GraphNodesConfig(Config):
    save_subgraphs: bool = Field(
        default=False,
        description=("Save subgraphs to disk in .graphml format for debugging."),
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "skeleton_claims": AssetIn(
            key=["skeleton_claims"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def graph_nodes(
    context: AssetExecutionContext,
    config: GraphNodesConfig,
    skeleton_claims: pl.DataFrame,
):
    logger = context.log
    logger.info(f"Processing {skeleton_claims.height} conversations...")

    df = skeleton_claims

    # Helper function to explode nested lists and add node_type
    def explode_node_type(df: pl.DataFrame, node_type_col: str) -> pl.DataFrame:
        return (
            df.select(
                [
                    "conversation_id",
                    pl.col("start_date").alias("date"),
                    pl.col(node_type_col).alias("nodes"),
                    pl.lit(node_type_col.rstrip("s")).alias("node_type"),
                    pl.col("cluster_label"),
                    pl.col("category"),
                    pl.col("is_personal"),
                ]
            )
            .explode("nodes")
            .select(
                [
                    "conversation_id",
                    "date",
                    "node_type",
                    pl.col("nodes").struct.field("description").alias("description"),
                    pl.col("nodes").struct.field("label").alias("label"),
                    (
                        pl.col("nodes").struct.field("time")
                        if node_type_col == "observables"
                        else pl.lit(None)
                    ).alias("time"),
                    "cluster_label",
                    "category",
                    "is_personal",
                ]
            )
            .sort(["description", "node_type"])
            .with_columns(
                duplicate_count=pl.col("label").cum_count().over("label"),
            )
            .with_columns(
                label=pl.when(pl.col("duplicate_count") == 1)
                .then(pl.col("label"))
                .otherwise(
                    pl.concat_str(
                        [
                            pl.col("label"),
                            pl.lit("_"),
                            pl.col("duplicate_count").cast(pl.Utf8),
                        ]
                    )
                ),
                old_label=pl.col("label"),
            )
            .drop("duplicate_count")
        )

    # Explode each node_type into separate dataframes
    speculatives_df = explode_node_type(df, "speculatives")
    inferrables_df = explode_node_type(df, "inferrables")
    observables_df = explode_node_type(df, "observables")

    # Combine all categories
    result = pl.concat([observables_df, speculatives_df, inferrables_df]).filter(
        pl.col("description").is_not_null() & pl.col("label").is_not_null()
    )

    # Create a mapping dictionary for each conversation
    label_mappings = (
        result.select(["conversation_id", "old_label", "label"]).unique().to_dicts()
    )

    # Group mappings by conversation_id
    conversation_mappings = {}
    for row in label_mappings:
        conv_id = row["conversation_id"]
        if conv_id not in conversation_mappings:
            conversation_mappings[conv_id] = {}
        conversation_mappings[conv_id][row["old_label"]] = row["label"]

    # Function to update labels in causal relationships
    def update_and_filter_relationships(
        relationships: list, mapping: dict, current_label: str
    ) -> list:
        updated_relationships = []
        for rel in relationships:
            updated_rel = {
                "source": mapping.get(rel["source"], rel["source"]),
                "target": mapping.get(rel["target"], rel["target"]),
            }
            # Only include relationships where current_label is source or target
            if (
                updated_rel["source"] == current_label
                or updated_rel["target"] == current_label
            ):
                updated_relationships.append(updated_rel)

        return updated_relationships

    # Apply the mapping to causal relationships if the column exists
    if "causal_relationships" in df.columns:
        result = result.join(
            df.select(["conversation_id", "causal_relationships"]),
            on="conversation_id",
        ).with_columns(
            causal_relationships=pl.struct(
                ["conversation_id", "causal_relationships", "label"]
            ).map_elements(
                lambda x: update_and_filter_relationships(
                    x["causal_relationships"],
                    conversation_mappings.get(x["conversation_id"], {}),
                    x["label"],
                )
            )
        )

    working_dir = DAGSTER_STORAGE_DIRECTORY / "graph_nodes"
    if config.save_subgraphs:
        logger.info("Saving subgraphs to disk...")
        working_dir.mkdir(parents=True, exist_ok=True)
        G = nx.DiGraph()

        for row in result.to_dicts():
            G.add_node(
                row["label"],
                type=row["node_type"],
                description=row["description"],
                date=row["date"],
                time=row["time"],
            )

            if "causal_relationships" in row:
                for edges in row["causal_relationships"]:
                    for edge in edges:
                        G.add_edge(edge["source"], edge["target"])

        nx.write_graphml(G, working_dir / f"{context.partition_key}.graphml")

    logger.info(f"Generated {result.height} graph nodes")
    return result
