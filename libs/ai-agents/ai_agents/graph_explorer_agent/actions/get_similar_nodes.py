from contextlib import nullcontext
from threading import Semaphore

import faiss
import networkx as nx
import numpy as np

from ai_agents.embeddings.base_embedder_client import BaseEmbedderClient

from ..types import AdjacencyList, AdjacencyListRecord

similarity_semaphore = Semaphore(1)


async def get_similar_nodes(
    G: nx.DiGraph,
    label_embeddings: list[dict],  # [{"id": <node_id>, "embedding": <vec>}]
    embedder_client: BaseEmbedderClient,
    query: str,
    top_k: int = 10,
    threshold: float = 0.6,
    use_lock: bool = True,
) -> AdjacencyList:
    # Use semaphore if running locally bc we can get only 1 embedding at a time
    lock = similarity_semaphore if use_lock else nullcontext()

    with lock:
        # Extract node IDs and embeddings in a consistent order
        node_ids = [d["id"] for d in label_embeddings]
        embeddings = np.array(
            [d["embedding"] for d in label_embeddings], dtype=np.float32
        )

        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms  # in-place normalization

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)  # type: ignore

        cost, query_embeddings = await embedder_client.get_embeddings([query])
        query_embedding = np.array(query_embeddings[0], dtype=np.float32).reshape(1, -1)

        # Normalize query as well
        query_embedding = query_embedding / np.linalg.norm(
            query_embedding, axis=1, keepdims=True
        )

        # Perform similarity search. For efficiency, ask for top_k directly
        scores, idxs = index.search(query_embedding, top_k)  # type: ignore
        scores, idxs = scores[0], idxs[0]  # unwrap since we only had 1 query

        # Filter by threshold
        filtered = [
            (idx, score) for (idx, score) in zip(idxs, scores) if score >= threshold
        ]

        result = []
        for i, _score in filtered:
            node_id = node_ids[i]
            node_data = G.nodes[node_id]

            record = AdjacencyListRecord(
                id=node_id,
                description=node_data.get("description", ""),
                datetime=node_data.get("datetime", None),
                frequency=node_data.get("frequency", 1),
                parents_count=len(list(G.predecessors(node_id))),
                children_count=len(list(G.successors(node_id))),
            )
            result.append(record)

    return result
