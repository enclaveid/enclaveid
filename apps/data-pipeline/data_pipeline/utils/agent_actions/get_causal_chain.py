import igraph as ig
import numpy as np
import polars as pl

from data_pipeline.resources.graph_explorer_agent.types import (
    AdjacencyList,
    AdjacencyListRecord,
    NodeReference,
)


def get_causal_chain(
    graph_nodes: pl.DataFrame, node_id: str, target_node_id: str, top_k: int = 30
) -> AdjacencyList:
    """
    Find a causal chain between two nodes using personalized PageRank.

    Args:
        graph_nodes: DataFrame containing node information and embeddings
        node_id: ID of the first node
        target_node_id: ID of the second node

    Returns:
        List of AdjacencyListRecord representing the causal chain
    """
    # Create graph from the dataframe
    edges = []
    for row in graph_nodes.iter_rows(named=True):
        for parent in row["parents"]:
            edges.append((parent["id"], row["id"]))
        for child in row["children"]:
            edges.append((row["id"], child["id"]))

    # Create igraph Graph
    unique_nodes = list(set(graph_nodes["id"]))
    node_to_idx = {node: idx for idx, node in enumerate(unique_nodes)}

    G = ig.Graph(directed=False)
    G.add_vertices(len(unique_nodes))
    G.add_edges([(node_to_idx[src], node_to_idx[dst]) for src, dst in edges])

    # Set up personalization vector focused on both nodes
    # NB: we split the probability of 1.0 between the two nodes
    # TODO: what if we distriubte the probability between other similar nodes?
    personalization = np.zeros(len(unique_nodes))
    personalization[node_to_idx[node_id]] = 0.5
    personalization[node_to_idx[target_node_id]] = 0.5

    # Run personalized PageRank
    pagerank_scores = G.personalized_pagerank(
        damping=0.85,  # Same alpha as in speculatives_substantiation
        reset=personalization,
        implementation="prpack",
    )

    # Get top scoring nodes and sort by PageRank score
    scored_nodes = [(unique_nodes[i], score) for i, score in enumerate(pagerank_scores)]
    scored_nodes.sort(key=lambda x: x[1], reverse=True)

    # Convert top nodes to AdjacencyListRecord format
    result = []
    for node_id, _ in scored_nodes[:top_k]:
        node_data = graph_nodes.filter(pl.col("id") == node_id).row(0, named=True)
        record = AdjacencyListRecord(
            id=node_data["id"],
            description=node_data["description"],
            datetime=node_data["datetime"],
            parents=[
                NodeReference(id=p.id, datetime=p.datetime)
                for p in node_data["parents"]
            ],
            children=[
                NodeReference(id=c.id, datetime=c.datetime)
                for c in node_data["children"]
            ],
        )
        result.append(record)

    return result
