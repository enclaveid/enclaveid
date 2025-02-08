from typing import Literal

import networkx as nx

from ai_agents.graph_explorer_agent.types import AdjacencyList, AdjacencyListRecord
from ai_agents.graph_explorer_agent.utils.get_node_datetime import get_node_datetime


def get_children(graph: nx.DiGraph, node_id: str) -> AdjacencyList:
    return _get_relatives(graph, node_id, mode="out")


def get_parents(graph: nx.DiGraph, node_id: str) -> AdjacencyList:
    return _get_relatives(graph, node_id, mode="in")


def _get_relatives(
    graph: nx.DiGraph, node_id: str, mode: Literal["in", "out"] = "out"
) -> AdjacencyList:
    if node_id not in graph:
        return []  # Return empty list if node not found

    # Get all ancestors/descendants up to specified depth
    if mode == "out":
        relatives = graph.successors(node_id)
    else:
        relatives = graph.predecessors(node_id)

    result: AdjacencyList = []

    # Process each relative
    for rel_id in relatives:
        record = AdjacencyListRecord(
            id=rel_id,
            description=graph.nodes(data=True)[rel_id].get("description", ""),
            datetime=get_node_datetime(
                graph.nodes(data=True)[rel_id].get("datetime", [])
            ),
            frequency=graph.nodes(data=True)[rel_id].get("frequency", 1),
        )

        result.append(record)

    return result


if __name__ == "__main__":
    import polars as pl

    filename = "/Users/ma9o/Desktop/enclaveid/apps/data-pipeline/data/dagster/whatsapp_nodes_deduplicated/00393494197577/0034689896443.snappy"
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

    print(len(get_children(G, "Relationship_Problems")))
