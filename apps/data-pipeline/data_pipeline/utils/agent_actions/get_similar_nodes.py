import faiss
import numpy as np
import polars as pl

from data_pipeline.resources.graph_explorer_agent.types import (
    AdjacencyList,
    AdjacencyListRecord,
    NodeReference,
)


def get_similar_nodes(
    graph_nodes: pl.DataFrame, query: str, top_k: int = 30
) -> AdjacencyList:
    embeddings = np.array(
        graph_nodes.get_column("embedding").to_list(), dtype=np.float32
    )

    # Create FAISS index for cosine similarity
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Convert query to numpy array and normalize
    query_embedding = np.array(query, dtype=np.float32).reshape(1, -1)
    faiss.normalize_L2(query_embedding)

    # Perform similarity search
    _, indices = index.search(query_embedding, top_k)
    similar_nodes: pl.DataFrame = graph_nodes[indices[0]]

    # Convert to AdjacencyList format
    result = []
    for row in similar_nodes.iter_rows(named=True):
        record = AdjacencyListRecord(
            id=row["label"],
            description=row["description"],
            datetime=row["datetime"],
            parents=[
                NodeReference(id=p["id"], datetime=p["datetime"])
                for p in row["parents"]
            ],
            children=[
                NodeReference(id=c["id"], datetime=c["datetime"])
                for c in row["children"]
            ],
        )
        result.append(record)

    return result
