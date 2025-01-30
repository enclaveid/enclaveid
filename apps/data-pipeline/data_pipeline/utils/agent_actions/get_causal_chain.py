import networkx as nx

from data_pipeline.resources.graph_explorer_agent.types import (
    AdjacencyList,
    AdjacencyListRecord,
    NodeReference,
)
from data_pipeline.utils.get_node_datetime import get_node_datetime


def get_causal_chain(
    G: nx.DiGraph, node_id: str, target_node_id: str, top_k: int = 30
) -> AdjacencyList:
    """
    Find a causal chain between two nodes using personalized PageRank.

    Args:
        G: NetworkX DiGraph containing the graph
        node_id: ID of the first node
        target_node_id: ID of the second node
        top_k: Number of top nodes to return

    Returns:
        List of AdjacencyListRecord representing the causal chain
    """

    # Calculate weights based on inverse frequencies
    weight1 = 1.0 / G.nodes[node_id]["frequency"]
    weight2 = 1.0 / G.nodes[target_node_id]["frequency"]

    # Normalize weights to sum to 1
    total_weight = weight1 + weight2
    # Set up personalization dictionary focused on both nodes
    personalization = {node: 0.0 for node in G.nodes()}
    personalization[node_id] = weight1 / total_weight
    personalization[target_node_id] = weight2 / total_weight

    # Run personalized PageRank
    pagerank_scores = nx.pagerank(
        G,
        alpha=0.85,  # Same alpha as before
        personalization=personalization,
    )

    # Get top scoring nodes and sort by PageRank score
    scored_nodes = [(node, score) for node, score in pagerank_scores.items()]
    scored_nodes.sort(key=lambda x: x[1], reverse=True)

    # Convert top nodes to AdjacencyListRecord format
    result = []
    for node_id, _ in scored_nodes[:top_k]:
        node_data = G.nodes(data=True)[node_id]
        record = AdjacencyListRecord(
            id=node_id,
            description=node_data.get("description", ""),
            datetime=node_data.get("datetime", None),
            parents=[
                NodeReference(
                    id=p, datetime=G.nodes(data=True)[p].get("datetime", None)
                )
                for p in G.predecessors(node_id)
            ],
            children=[
                NodeReference(
                    id=c, datetime=G.nodes(data=True)[c].get("datetime", None)
                )
                for c in G.successors(node_id)
            ],
            frequency=node_data.get("frequency", 1),
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

    print(
        get_causal_chain(
            G, "dismissive_resolution", "relationship_with_humor_and_independence"
        )
    )
