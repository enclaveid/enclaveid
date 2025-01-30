import faiss
import networkx as nx
import numpy as np

from data_pipeline.resources.batch_embedder_resource import BatchEmbedderResource
from data_pipeline.resources.graph_explorer_agent.types import (
    AdjacencyList,
    AdjacencyListRecord,
    NodeReference,
)


def get_similar_nodes(
    G: nx.DiGraph,
    label_embeddings: list[dict],
    batch_embedder: BatchEmbedderResource,
    query: str,
    top_k: int = 7,
) -> AdjacencyList:
    embeddings = np.array([d["embedding"] for d in label_embeddings], dtype=np.float32)

    # Create FAISS index for cosine similarity
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)  # type: ignore

    cost, query_embeddings = batch_embedder.get_embeddings_sync([query])
    query_embedding = np.array(query_embeddings[0], dtype=np.float32).reshape(1, -1)

    # Perform similarity search
    _, indices = index.search(query_embedding, min(top_k, len(embeddings)))  # type: ignore
    # Get nodes by index - networkx doesn't have direct index access, so we'll get all nodes first
    all_nodes = list(G.nodes(data=True))
    similar_nodes = [all_nodes[i] for i in indices[0]]

    # Convert to AdjacencyList format
    result = []
    for node_id, node_data in similar_nodes:
        record = AdjacencyListRecord(
            id=node_id,  # NetworkX uses node IDs directly
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
