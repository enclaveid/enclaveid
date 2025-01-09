from collections import defaultdict
from time import time

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
from data_pipeline.utils.get_working_dir import get_working_dir


class SpeculativesSubstantiationConfig(Config):
    row_limit: int | None = None if get_environment() == "LOCAL" else None
    top_k: int = Field(default=30, description="Number of similar nodes to return")
    personalization_threshold: float = Field(
        default=0.7,
        description="Similarity threshold for a node to get assigned a personalization score during PageRank",
    )
    alpha: float = Field(default=0.85, description="PageRank damping parameter")
    batch_size: int = Field(default=1000, description="Batch size for FAISS queries")
    benchmark_baseline_rag: bool = Field(
        default=True, description="Save the baseline RAG results to compare"
    )


def create_faiss_index(graph_nodes: pl.DataFrame) -> faiss.IndexFlatIP:
    """Create and populate FAISS index from graph node embeddings."""
    embeddings = np.stack(graph_nodes.get_column("embedding").to_list())
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))  # type: ignore
    return index


def get_baseline_results(
    graph_nodes: pl.DataFrame,
    max_similarities: dict[int, float],
    config: SpeculativesSubstantiationConfig,
):
    """Get baseline RAG results if enabled.

    Instead of a direct FAISS top_k (for a single embedding),
    we use the `max_similarities` dictionary: node_idx -> similarity.
    We’ll select the top_k nodes by similarity.
    """
    if not config.benchmark_baseline_rag:
        return None

    # Sort node indices by max similarity
    top_node_indices = sorted(
        max_similarities.keys(),
        key=lambda idx: max_similarities[idx],
        reverse=True,
    )[: config.top_k]

    results = []
    for idx in top_node_indices:
        node = graph_nodes.row(idx, named=True)
        results.append(
            {
                "label": node["label"],
                "score": float(max_similarities[idx]),
                "category": node["category"],
                "node_type": node["node_type"],
                "description": node["description"],
            }
        )

    return results


def calculate_personalization_vector(
    G: ig.Graph,
    max_similarities: dict[int, float],
    label_indices: np.ndarray,
    vertex_indices: np.ndarray,
    config: SpeculativesSubstantiationConfig,
):
    """Calculate personalization vector for PageRank using the aggregated (max) similarities.

    `max_similarities` is a dict of {graph_node_index_in_faiss: similarity}.
    """
    personalization = np.zeros(len(G.vs))

    # For each vertex in the graph, figure out which row in graph_nodes it corresponds to.
    # The array `label_indices` tells us which index of graph_nodes each vertex maps to.
    # If label_indices[v] == -1, that vertex doesn't match anything in graph_nodes.
    # If label_indices[v] != -1, it's the row in graph_nodes that vertex corresponds to.
    # We see if that row is in our max_similarities dictionary.
    for v_idx in range(len(G.vs)):
        graph_node_row_idx = label_indices[v_idx]
        if graph_node_row_idx in max_similarities:
            sim = max_similarities[graph_node_row_idx]
            if sim < config.personalization_threshold:
                continue
            freq = G.vs[v_idx]["frequency"]
            personalization[v_idx] = sim * (1.0 / freq)

    return personalization


def get_scored_nodes(
    G: ig.Graph, pagerank_scores: list[float], config: SpeculativesSubstantiationConfig
):
    """Get sorted scored nodes."""
    return sorted(
        [
            (
                v["id"],
                v["category"],
                v["node_type"],
                v["description"],
                score,
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
    config: SpeculativesSubstantiationConfig,
) -> pl.DataFrame:
    """
    Restructured so that if there are multiple embeddings for a single query `label`, we
    combine their FAISS similarities by taking the maximum similarity per graph node.
    The rest of the PageRank logic remains similar.
    """
    # Slice queries for debugging or limited run
    query_nodes = speculatives_query_entities_w_embeddings.slice(0, config.row_limit)
    # Only keep real nodes (non-speculative) in the graph
    graph_nodes = recursive_causality.filter(pl.col("node_type") != "speculative")

    working_dir = get_working_dir(context) / ".." / "recursive_causality"
    G: ig.Graph = ig.Graph.Read_GraphML(
        str(working_dir / f"{context.partition_key}.graphml")
    )

    context.log.info(f"Graph has {G.vcount()} nodes and {G.ecount()} edges")

    # Create FAISS index from all the graph nodes
    index = create_faiss_index(graph_nodes)

    # Create a lookup that tells us, for each row in graph_nodes, which label it corresponds to
    label_to_idx = {
        label: idx for idx, label in enumerate(graph_nodes.get_column("label"))
    }

    # We'll use this to map from graph vertex to an index in graph_nodes
    vertex_ids = np.array([v["id"] for v in G.vs])
    label_indices = np.array([label_to_idx.get(vid, -1) for vid in vertex_ids])
    vertex_indices = np.arange(len(G.vs))

    # First get the speculative nodes
    speculative_nodes = recursive_causality.select(
        pl.col("label"),
        pl.col("node_type"),
        pl.col("category"),
    ).filter(pl.col("node_type") == "speculative")

    # Join query nodes with speculative nodes before grouping
    grouped_query = (
        query_nodes.join(speculative_nodes, on="label", how="left")
        .group_by("label", "description", "category", maintain_order=True)
        .agg(
            [
                pl.col("embedding").alias("embeddings"),
            ]
        )
    )

    results = []
    start_time = time()
    last_log_time = start_time

    total_labels = len(grouped_query)
    total_processed = 0

    context.log.info(
        f"Processing {total_labels} unique query labels in batches of {config.batch_size}..."
    )

    # We will process grouped labels in "batches" as well,
    # primarily to limit memory usage if you have many labels.
    for batch_start in range(0, total_labels, config.batch_size):
        batch_end = min(batch_start + config.batch_size, total_labels)
        batch_df = grouped_query.slice(batch_start, batch_end - batch_start)

        # We won't use the older process_batch_pagerank() directly,
        # but the logic is nearly identical.
        for row in batch_df.iter_rows(named=True):
            embeddings_list = row["embeddings"]  # all embeddings for this label

            curr_node = {
                "label": row["label"],
                "node_type": "speculative",
                "description": row["description"],
                "category": row["category"],
            }

            # Convert embeddings_list (List of arrays) into a single 2D numpy array
            # shape = (M, dimension)
            query_embeddings = np.stack(embeddings_list)

            # 1) Search each of the M embeddings in FAISS
            # 2) Collect the maximum similarity for each returned index
            #    across all embeddings.
            max_similarities: dict[int, float] = defaultdict(float)

            for emb in query_embeddings:
                # shape(1, dim) for current embedding
                emb_2d = emb[np.newaxis, :]
                D, I = index.search(emb_2d.astype(np.float32), len(graph_nodes))
                # D, I shapes: (1, k)
                for idx_in_faiss, sim in zip(I[0], D[0]):
                    if sim > max_similarities[idx_in_faiss]:
                        max_similarities[idx_in_faiss] = sim

            # If baseline is enabled, let's also build a baseline list for debug.
            baseline_similar_nodes = get_baseline_results(
                graph_nodes, max_similarities, config
            )

            # Build personalization vector from these aggregated similarities
            personalization = calculate_personalization_vector(
                G, max_similarities, label_indices, vertex_indices, config
            )

            result_dict = {}

            if np.sum(personalization) == 0:
                # Get top-k nodes sorted by similarity
                top_k_nodes = [
                    {
                        "label": graph_nodes.row(idx, named=True)["label"],
                        "description": graph_nodes.row(idx, named=True)["description"],
                        "category": graph_nodes.row(idx, named=True)["category"],
                        "node_type": graph_nodes.row(idx, named=True)["node_type"],
                        "score": sim,
                    }
                    for idx, sim in sorted(
                        max_similarities.items(), key=lambda x: x[1], reverse=True
                    )[: config.top_k]
                ]

                result_dict = {
                    **curr_node,
                    "success": False,
                    "similar_nodes": top_k_nodes,
                }
            else:
                # Run personalized PageRank
                pagerank_start_time = time()
                pagerank_scores = G.personalized_pagerank(
                    damping=config.alpha,
                    reset=personalization,
                    implementation="prpack",
                    directed=False,  # ?
                )
                pagerank_time = time() - pagerank_start_time

                # Sort and retrieve top-k nodes
                scored_nodes = get_scored_nodes(G, pagerank_scores, config)

                result_dict = {
                    **curr_node,
                    "success": True,
                    "similar_nodes": [
                        {
                            "label": node,
                            "score": score,
                            "category": category,
                            "node_type": node_type,
                            "description": description,
                        }
                        for (
                            node,
                            category,
                            node_type,
                            description,
                            score,
                        ) in scored_nodes
                    ],
                }

            if config.benchmark_baseline_rag:
                result_dict["similar_nodes_baseline"] = baseline_similar_nodes

            results.append(result_dict)

        total_processed = batch_end
        current_time = time()
        if current_time - last_log_time >= 30:
            elapsed_time = current_time - start_time
            progress = total_processed / total_labels
            estimated_total_time = elapsed_time / progress
            remaining_time = estimated_total_time - elapsed_time

            context.log.info(
                f"{total_processed}/{total_labels} labels ({progress:.1%}) | "
                f"Est. remaining time: {remaining_time/60:.1f}min | "
                f"Last PageRank took ~{pagerank_time*1000:.1f}ms"
            )
            last_log_time = current_time

    # Final stats
    total_time = (time() - start_time) / 60
    context.log.info(
        f"Completed processing {total_labels} labels | Total time: {total_time:.1f}min."
    )

    result = pl.DataFrame(results)

    failed_queries_count = result.filter(pl.col("success") == False).height

    context.log.info(f"Failed queries: {failed_queries_count}/{result.height}.")

    return result
