import networkx as nx
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import DAGSTER_STORAGE_DIRECTORY
from data_pipeline.partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    ins={
        "deduplicated_graph_w_embeddings": AssetIn(
            key=["deduplicated_graph_w_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def base_graph(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    deduplicated_graph_w_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    df = deduplicated_graph_w_embeddings
    working_dir = DAGSTER_STORAGE_DIRECTORY / "base_graph"

    # Initialize directed graph
    G = nx.DiGraph()

    # Add nodes and edges from the new format
    for row in df.iter_rows(named=True):
        # Add node with its attributes
        G.add_node(
            row["label"],
            description=(row["description"]),
            category=row["category"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            conversation_id=row["conversation_id"],
            cluster_label=row["cluster_label"],
            is_personal=row["is_personal"],
            node_type=row["node_type"],
        )

        # Add edges for this node
        for target in row["edges"]:
            G.add_edge(row["label"], target)

    # Create output directory if it doesn't exist
    working_dir.mkdir(parents=True, exist_ok=True)

    # Find nodes with degree 0
    isolated_nodes = [
        (
            node,
            data["description"],
            data["category"],
            data["start_date"],
            data["end_date"],
            data["conversation_id"],
            data["cluster_label"],
            data["is_personal"],
            data["node_type"],
        )
        for node, data in G.nodes(data=True)
        if G.degree(node) == 0  # type: ignore
    ]

    # Remove isolated nodes from the graph
    G.remove_nodes_from([node[0] for node in isolated_nodes])

    # Save graph in GraphML format
    nx.write_graphml(G, working_dir / f"{context.partition_key}.graphml")

    # Save reversed graph in GraphML format
    nx.write_graphml(
        G.reverse(), working_dir / f"{context.partition_key}_reversed.graphml"
    )

    # Return a dataframe of isolated nodes and previously unassigned speculative claims
    return pl.DataFrame(
        isolated_nodes,
        schema=[
            "label",
            "description",
            "category",
            "start_date",
            "end_date",
            "conversation_id",
            "cluster_label",
            "is_personal",
            "node_type",
        ],
    )
