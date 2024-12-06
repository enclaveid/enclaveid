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
    },
    io_manager_key="parquet_io_manager",
)
def base_graph_manual(
    context: AssetExecutionContext,
    deduplicated_graph_raw: pl.DataFrame,
) -> None:
    df = deduplicated_graph_raw
    working_dir = (
        PRODUCTION_STORAGE_BUCKET / "base_graph_manual" / context.partition_key
    )

    # Initialize directed graph
    G = nx.DiGraph()

    for row in df.iter_rows(named=True):
        # Add nodes from observables and inferrables with their descriptions
        for entity in row["observables"]:
            G.add_node(
                entity["label"],
                description=entity["description"],
                category="observable",
            )
        for entity in row["inferrables"]:
            G.add_node(
                entity["label"],
                description=entity["description"],
                category="inferrable",
            )

        # Parse and add edges from causal_relationships
        try:
            edges = row["causal_relationships"]
            for edge in edges:
                G.add_edge(edge["source"], edge["target"])
        except Exception as e:
            context.log.warning(f"Failed to parse causal relationships: {e}")
            continue

    # Create output directory if it doesn't exist
    working_dir.mkdir(parents=True, exist_ok=True)

    # Save graph in GraphML format
    nx.write_graphml(G, working_dir / "graph.graphml")
