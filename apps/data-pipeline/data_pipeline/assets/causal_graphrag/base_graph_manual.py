import networkx as nx
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.consts import PRODUCTION_STORAGE_BUCKET
from data_pipeline.partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    ins={
        "deduplicated_graph_raw": AssetIn(
            key=["deduplicated_graph_raw"],
        ),
        "conversation_claims": AssetIn(
            key=["conversation_claims"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def base_graph_manual(
    context: AssetExecutionContext,
    deduplicated_graph_raw: pl.DataFrame,
    conversation_claims: pl.DataFrame,
) -> pl.DataFrame:
    df = deduplicated_graph_raw
    working_dir = PRODUCTION_STORAGE_BUCKET / "base_graph_manual"

    # Initialize directed graph
    G = nx.DiGraph()

    # Add nodes and edges from the new format
    for row in df.iter_rows(named=True):
        # Add node with its attributes
        G.add_node(
            row["label"],
            description=row["description"],
            category=row["category"],
        )

        # Add edges for this node
        for target in row["edges"]:
            G.add_edge(row["label"], target)

    # Create output directory if it doesn't exist
    working_dir.mkdir(parents=True, exist_ok=True)

    # Find nodes with degree 0
    isolated_nodes = [
        (node, data["description"], data["category"])
        for node, data in G.nodes(data=True)
        if G.degree(node) == 0
    ]

    # Remove isolated nodes from the graph
    G.remove_nodes_from([node for node, _, _ in isolated_nodes])

    # Save graph in GraphML format
    nx.write_graphml(G, working_dir / f"{context.partition_key}.graphml")

    # Return a dataframe of isolated nodes and previously unassigned speculative claims
    return pl.DataFrame(
        isolated_nodes,
        schema=["label", "description", "category"],
    ).vstack(
        conversation_claims.select(
            [
                pl.col("speculatives")
                .list.explode()
                .struct.field("label")
                .alias("label"),
                pl.col("speculatives")
                .list.explode()
                .struct.field("description")
                .alias("description"),
                pl.lit("speculative").alias("category"),
            ]
        ).unique()
    )
