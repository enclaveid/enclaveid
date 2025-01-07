import networkx as nx
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.constants.environments import DAGSTER_STORAGE_DIRECTORY
from data_pipeline.partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    ins={
        "base_graph": AssetIn(
            key=["base_graph"],
        ),
        "speculatives_causality": AssetIn(
            key=["speculatives_causality"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def final_graph(
    context: AssetExecutionContext,
    base_graph: pl.DataFrame,
    speculatives_causality: pl.DataFrame,
) -> pl.DataFrame:
    working_dir = DAGSTER_STORAGE_DIRECTORY / "final_graph"
    working_dir.mkdir(parents=True, exist_ok=True)

    # Load the base graph from GraphML
    base_graph_path = (
        DAGSTER_STORAGE_DIRECTORY / "base_graph" / f"{context.partition_key}.graphml"
    )
    G = nx.read_graphml(base_graph_path)

    # Process speculative claims and their causality analysis
    for row in speculatives_causality.iter_rows(named=True):
        # Add the speculative node if it has valid causality analysis
        if row["causality"] and isinstance(row["causality"], list):
            # Add the speculative node with its attributes
            G.add_node(
                row["label"],
                description=row["description"],
                category="speculative",
                start_date=row["start_date"],
                end_date=row["end_date"],
            )

            # Add edges based on causality analysis
            for causal_link in row["causality"]:
                target_label = causal_link["label"]
                if target_label in G:
                    # Add edge from the speculative node to its effect
                    G.add_edge(row["label"], target_label)

    # Save the final graph
    nx.write_graphml(G, working_dir / f"{context.partition_key}.graphml")

    # Convert graph to DataFrame for output
    nodes_data = []
    for node, data in G.nodes(data=True):
        nodes_data.append(
            {
                "label": node,
                "description": data["description"],
                "category": data["category"],
                "start_date": data["start_date"],
                "end_date": data["end_date"],
                "in_degree": G.in_degree(node),
                "out_degree": G.out_degree(node),
            }
        )

    return pl.DataFrame(nodes_data)
