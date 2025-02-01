from typing import Literal

import networkx as nx

from data_pipeline.utils.agents.graph_explorer_agent.types import (
    AdjacencyList,
    AdjacencyListRecord,
)
from data_pipeline.utils.get_node_datetime import get_node_datetime


def get_children(graph: nx.DiGraph, node_id: str, depth: int = 1) -> AdjacencyList:
    return _get_relatives(graph, node_id, mode="out", depth=depth)


def get_parents(graph: nx.DiGraph, node_id: str) -> AdjacencyList:
    return _get_relatives(graph, node_id, mode="in")


def _get_relatives(
    graph: nx.DiGraph, node_id: str, mode: Literal["in", "out"] = "out", depth: int = 1
) -> AdjacencyList:
    if node_id not in graph:
        return []  # Return empty list if node not found

    # Get all ancestors/descendants up to specified depth
    if mode == "out":
        relatives = nx.descendants_at_distance(graph, node_id, depth)
    else:
        relatives = nx.ancestors(graph, node_id)

    result: AdjacencyList = []

    # Process each relative
    for rel_id in relatives:
        # Get parent and child references
        # parents = [
        #     NodeReference(
        #         id=parent,
        #         datetime=graph.nodes(data=True)[parent].get("datetime", None),
        #     )
        #     for parent in graph.predecessors(rel_id)
        # ]

        # children = [
        #     NodeReference(
        #         id=child,
        #         datetime=graph.nodes(data=True)[child].get("datetime", None),
        #     )
        #     for child in graph.successors(rel_id)
        # ]

        # Create record for this node
        record = AdjacencyListRecord(
            id=rel_id,
            description=graph.nodes(data=True)[rel_id].get("description", ""),
            datetime=graph.nodes(data=True)[rel_id].get("datetime", None),
            frequency=graph.nodes(data=True)[rel_id].get("frequency", 1),
            parents_count=len(list(graph.predecessors(rel_id))),
            children_count=len(list(graph.successors(rel_id))),
        )

        result.append(record)

    return result


if __name__ == "__main__":
    import polars as pl

    filename = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_nodes_deduplicated/cm0i27jdj0000aqpa73ghpcxf.snappy"
    df = pl.read_parquet(filename)

    G = nx.DiGraph()
    for row in df.iter_rows(named=True):
        G.add_node(
            row["id"],
            description=row["proposition"],
            frequency=row["frequency"],
            user=row["user"],
            datetime=get_node_datetime(row["datetimes"]),
            chunk_ids=row["chunk_ids"],
        )
        G.add_edges_from([(row["id"], e) for e in row["edges"]])

    print(get_children(G, "frequent_check_ins", 1))
