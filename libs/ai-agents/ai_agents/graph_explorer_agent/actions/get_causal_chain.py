import networkx as nx

from ..types import AdjacencyList, AdjacencyListRecord
from ..utils.get_node_datetime import get_node_datetime


def _get_pageranked_nodes(
    G: nx.DiGraph, node_id: str, target_node_id: str, top_k: int
) -> list[str]:
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

    node_ids = [x for x, _ in scored_nodes[:top_k]]

    return node_ids


def get_causal_chain(
    G: nx.DiGraph, node_id: str, target_node_id: str, top_k: int = 10
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

    try:
        print(node_id, target_node_id)
        node_ids = nx.shortest_path(G, node_id, target_node_id)

    except nx.NetworkXNoPath:
        print("No shortest path")
        # If no shortest path, use pageranked nodes
        try:
            node_ids = _get_pageranked_nodes(G, node_id, target_node_id, top_k)
        except Exception as e:
            print(e)
            raise e

    # Convert top nodes to AdjacencyListRecord format
    result = []
    for node_id in node_ids:
        node_data = G.nodes(data=True)[node_id]
        record = AdjacencyListRecord(
            id=node_id,
            description=node_data.get("description", ""),
            datetime=node_data.get("datetime", None),
            frequency=node_data.get("frequency", 1),
            # parents_count=len(list(G.predecessors(node_id))),
            # children_count=len(list(G.successors(node_id))),
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

    print(get_causal_chain(G, "giovanni_commitment_phobia", "mutual frustration"))
