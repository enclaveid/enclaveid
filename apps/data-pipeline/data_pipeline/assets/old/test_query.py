from typing import Literal, cast

import faiss
import networkx as nx
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.constants.environments import DAGSTER_STORAGE_DIRECTORY
from data_pipeline.partitions import user_partitions_def


class TestQueryConfig(Config):
    top_k: int = Field(
        default=10,
        description="The number of nodes to return",
    )
    test_question: str = Field(
        default="What are the next things I could do to improve my life?",
        description="The question to ask the model",
    )
    edge_direction: Literal["upstream", "downstream", "both"] = Field(
        default="upstream",
        description="The direction of the edges to follow",
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "final_graph": AssetIn(
            key=["final_graph"],
        ),
        "deduplicated_graph_w_embeddings": AssetIn(
            key=["deduplicated_graph_w_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def test_query(
    context: AssetExecutionContext,
    final_graph: pl.DataFrame,
    deduplicated_graph_w_embeddings: pl.DataFrame,
    config: TestQueryConfig,
) -> None:
    # Load the graph from GraphML
    working_dir = DAGSTER_STORAGE_DIRECTORY / "final_graph"
    G: nx.DiGraph | nx.Graph = nx.read_graphml(
        working_dir / f"{context.partition_key}.graphml"
    )

    # Reverse the graph as we want to prioritize upstream nodes
    if config.edge_direction == "upstream":
        G = cast(nx.DiGraph, G).reverse()
    elif config.edge_direction == "downstream":
        pass
    elif config.edge_direction == "both":
        # Make the graph undirected
        G = G.to_undirected()

    # Prepare FAISS index with embeddings
    embeddings = np.stack(
        deduplicated_graph_w_embeddings.get_column("embedding").to_list()
    )
    faiss.normalize_L2(embeddings)

    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))

    # Create label to index mapping
    label_to_idx = {
        label: idx
        for idx, label in enumerate(deduplicated_graph_w_embeddings.get_column("label"))
    }

    # Get the embedding for the test question
    test_embedding = deduplicated_graph_w_embeddings.filter(
        pl.col("description") == config.test_question
    ).get_column("embedding")

    if len(test_embedding) == 0:
        context.log.error(
            f"Test question '{config.test_question}' not found in embeddings"
        )
        return

    test_embedding = test_embedding[0]

    # Search for similar nodes and apply PPR
    query = np.array([test_embedding]).astype(np.float32)
    faiss.normalize_L2(query)
    D, I = index.search(
        query, min(config.top_k * 2, len(deduplicated_graph_w_embeddings))
    )

    # Create personalization dict for PPR
    personalization = {}
    for node in G.nodes():
        if node in label_to_idx and label_to_idx[node] in I[0]:
            idx = np.where(I[0] == label_to_idx[node])[0][0]
            personalization[node] = max(0, D[0][idx])
        else:
            personalization[node] = 0

    # Run personalized PageRank
    pagerank_scores = nx.pagerank(G, alpha=0.85, personalization=personalization)

    # Get and print top k nodes
    top_nodes = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[
        : config.top_k
    ]

    context.log.info(
        f"\nTop {config.top_k} results for question: '{config.test_question}'"
    )
    for node, score in top_nodes:
        node_info = deduplicated_graph_w_embeddings.filter(pl.col("label") == node)
        context.log.info(
            f"\nNode: {node}"
            f"\nCategory: {node_info.get_column('category')[0]}"
            f"\nDescription: {node_info.get_column('description')[0]}"
            f"\nScore: {score:.4f}"
            f"\n---"
        )
