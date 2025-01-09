from time import time
from typing import Literal

import faiss
import igraph as ig
import numpy as np
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Config,
    asset,
)
from pydantic import Field

from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
)
from data_pipeline.utils.get_working_dir import get_working_dir


class SpeculativesSubstantiationConfig(Config):
    row_limit: int | None = None if get_environment() == "LOCAL" else None
    top_k: int = Field(default=100, description="Number of similar nodes to return")
    personalization_threshold: float = Field(
        default=0.7,
        description="Similarity threshold for a node to get assigned a personalization score during PageRank",
    )
    alpha: float = Field(default=0.85, description="PageRank damping parameter")
    batch_size: int = Field(default=1000, description="Batch size for FAISS queries")
    benchmark_baseline_rag: bool = Field(
        default=True, description="Save the baseline RAG results to compare"
    )
    direction: Literal["forward", "backward", "undirected"] = Field(
        default="undirected", description="Direction of the graph to search"
    )


def create_faiss_index(graph_nodes):
    """Create and populate FAISS index from graph node embeddings."""
    embeddings = np.stack(graph_nodes.get_column("embedding").to_list())
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))  # type: ignore
    return index


def get_baseline_results(graph_nodes, batch_idx, I, D, config):
    """Get baseline RAG results if enabled."""
    if not config.benchmark_baseline_rag:
        return None

    return [
        {
            "label": graph_nodes.row(i, named=True)["label"],
            "score": float(D[batch_idx][j]),
            "category": graph_nodes.row(i, named=True)["category"],
            "node_type": graph_nodes.row(i, named=True)["node_type"],
            "description": graph_nodes.row(i, named=True)["description"],
            "conversation_id": graph_nodes.row(i, named=True)["conversation_id"],
        }
        for j, i in enumerate(I[batch_idx][: config.top_k])
    ]


def calculate_personalization_vector(
    G, batch_idx, I, D, label_indices, vertex_indices, config
):
    """Calculate personalization vector for PageRank."""
    personalization = np.zeros(len(G.vs))
    mask = np.isin(label_indices, I[batch_idx])
    if mask.any():
        matched_label_indices = label_indices[mask]
        matched_vertex_indices = vertex_indices[mask]
        I_positions = np.array(
            [np.where(I[batch_idx] == idx)[0][0] for idx in matched_label_indices]
        )
        similarities = D[batch_idx][I_positions]
        similarities[similarities < config.personalization_threshold] = 0
        frequencies = np.array(
            [G.vs[idx]["frequency"] for idx in matched_vertex_indices]
        )
        similarities = similarities * (1.0 / frequencies)
        personalization[matched_vertex_indices] = similarities
    return personalization


def get_scored_nodes(G, pagerank_scores, config):
    """Get sorted scored nodes with frequency weighting."""
    return sorted(
        [
            (
                v["id"],
                v["category"],
                v["node_type"],
                v["description"],
                v["conversation_id"],
                score * (1.0 / v["frequency"]),
            )
            for v, score in zip(G.vs, pagerank_scores)
        ],
        key=lambda x: x[-1],
        reverse=True,
    )[: config.top_k]


@asset(
    partitions_def=user_partitions_def,
    ins={
        "recursive_causality": AssetIn(
            key=["recursive_causality"],
        ),
        "speculatives_query_entities_w_embeddings": AssetIn(
            key=["speculatives_query_entities_w_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def speculatives_substantiation(
    context: AssetExecutionContext,
    speculatives_query_entities_w_embeddings: pl.DataFrame,
    recursive_causality: pl.DataFrame,
    llama70b: BaseLlmResource,
    config: SpeculativesSubstantiationConfig,
) -> pl.DataFrame:
    query_nodes = speculatives_query_entities_w_embeddings.slice(0, config.row_limit)
    graph_nodes = recursive_causality.filter(pl.col("node_type") != "speculative")

    working_dir = get_working_dir(context)
    G: ig.Graph = ig.Graph.Read_GraphML(
        str(working_dir / f"{context.partition_key}.graphml")
    )

    context.log.info(f"Graph has {G.vcount()} nodes and {G.ecount()} edges")

    # Create FAISS index
    index = create_faiss_index(graph_nodes)

    # Create label to index mapping
    label_to_idx = {
        label: idx for idx, label in enumerate(graph_nodes.get_column("label"))
    }

    def process_batch_pagerank(query_embeddings, node_info_list):
        batch_size = len(query_embeddings)

        faiss_query_start_time = time()
        D, I = index.search(
            query_embeddings.astype(np.float32),
            min(config.top_k * 2, len(graph_nodes)),
        )
        faiss_query_time = time() - faiss_query_start_time

        batch_results = []
        total_pagerank_time = 0
        total_personalization_time = 0

        for batch_idx in range(batch_size):
            baseline_similar_nodes = get_baseline_results(
                graph_nodes, batch_idx, I, D, config
            )

            personalization_start_time = time()
            personalization = calculate_personalization_vector(
                G, batch_idx, I, D, label_indices, vertex_indices, config
            )
            total_personalization_time += time() - personalization_start_time

            pagerank_start_time = time()
            pagerank_scores = G.personalized_pagerank(
                damping=config.alpha,
                reset=personalization,
                implementation="prpack",
                directed=True,
            )
            total_pagerank_time += time() - pagerank_start_time

            scored_nodes = get_scored_nodes(G, pagerank_scores, config)

            similar_nodes = [
                {
                    "label": node,
                    "score": score,
                    "category": category,
                    "node_type": node_type,
                    "description": description,
                    "conversation_id": conversation_id,
                }
                for node, category, node_type, description, conversation_id, score in scored_nodes
            ]

            result_dict = {
                "label": node_info_list[batch_idx]["label"],
                "node_type": node_info_list[batch_idx]["node_type"],
                "description": node_info_list[batch_idx]["description"],
                "category": node_info_list[batch_idx]["category"],
                "conversation_id": node_info_list[batch_idx]["conversation_id"],
                "similar_nodes": similar_nodes,
            }

            if config.benchmark_baseline_rag:
                result_dict["similar_nodes_baseline"] = baseline_similar_nodes

            batch_results.append(result_dict)

        return (
            batch_results,
            total_pagerank_time,
            faiss_query_time,
            total_personalization_time,
        )

    # Before the main processing loop, add these lines:
    vertex_ids = np.array([v["id"] for v in G.vs])
    label_indices = np.array([label_to_idx.get(vid, -1) for vid in vertex_ids])
    vertex_indices = np.arange(len(G.vs))

    # Process query nodes in batches
    results = []

    start_time = time()
    last_log_time = start_time
    total_nodes = len(query_nodes)
    total_pagerank_time = 0
    total_faiss_query_time = 0
    total_personalization_time = 0

    context.log.info(
        f"Processing {total_nodes} query nodes in batches of {config.batch_size}..."
    )

    # Prepare all valid nodes and their embeddings
    valid_nodes = []
    valid_embeddings = []

    for row in query_nodes.iter_rows(named=True):
        node_embedding_df = graph_nodes.filter(pl.col("label") == row["label"])
        if node_embedding_df.height > 0:
            valid_nodes.append(row)
            valid_embeddings.append(node_embedding_df.get_column("embedding")[0])

    # Process in batches
    for batch_start in range(0, len(valid_nodes), config.batch_size):
        batch_end = min(batch_start + config.batch_size, len(valid_nodes))

        batch_embeddings = np.stack(valid_embeddings[batch_start:batch_end])
        batch_nodes = valid_nodes[batch_start:batch_end]

        (
            batch_results,
            pagerank_time,
            faiss_query_time,
            personalization_time,
        ) = process_batch_pagerank(batch_embeddings, batch_nodes)

        results.extend(batch_results)
        total_pagerank_time += pagerank_time
        total_faiss_query_time += faiss_query_time
        total_personalization_time += personalization_time

        current_time = time()
        if current_time - last_log_time >= 30:
            elapsed_time = current_time - start_time
            progress = batch_end / total_nodes
            estimated_total_time = elapsed_time / progress
            remaining_time = estimated_total_time - elapsed_time

            context.log.info(
                f"{batch_end}/{total_nodes} ({progress:.1%}) | "
                f"Est. remaining time: {remaining_time/60:.1f}min | "
                f"Avg PageRank time: {(total_pagerank_time/batch_end)*1000:.1f}ms | "
                f"Avg FAISS query time: {(total_faiss_query_time/batch_end)*1000:.1f}ms | "
                f"Avg Personalization time: {(total_personalization_time/batch_end)*1000:.1f}ms"
            )
            last_log_time = current_time

    # Final statistics
    context.log.info(
        f"Completed processing {total_nodes} nodes | "
        f"Total time: {(time() - start_time)/60:.1f}min | "
        f"Avg PageRank time: {(total_pagerank_time/len(results))*1000:.1f}ms | "
        f"Avg FAISS query time: {(total_faiss_query_time/len(results))*1000:.1f}ms | "
        f"Avg Personalization time: {(total_personalization_time/len(results))*1000:.1f}ms"
    )

    return pl.DataFrame(results)
