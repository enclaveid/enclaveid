from typing import Dict, List

import faiss
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def
from data_pipeline.utils.get_logger import get_logger

DEFAULT_THRESHOLD = 0.9


def create_node_mapping(
    original_nodes: List[Dict[str, str]],
    deduped_nodes: List[Dict[str, str]],
    embeddings: List[List[float]],
    threshold: float = DEFAULT_THRESHOLD,
) -> Dict[str, str]:
    """
    Creates a mapping from original node labels to their deduplicated versions using
    cosine similarity between embeddings.

    The cosine similarity between two vectors a and b is:
    cos(θ) = (a · b) / (||a|| ||b||)

    When vectors are L2-normalized, their dot product directly gives cosine similarity
    because ||a|| = ||b|| = 1, so cos(θ) = a · b
    """
    if not embeddings or not original_nodes:
        return {node["label"]: node["label"] for node in original_nodes}

    # Convert embeddings to numpy array
    embeddings_array = np.array(embeddings, dtype=np.float32)

    # L2 normalize the embeddings - this ensures dot product equals cosine similarity
    faiss.normalize_L2(embeddings_array)

    # Create FAISS index for normalized vectors
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_array)

    # Search for similar nodes
    # We use embeddings_array as queries against itself
    similarities, indices = index.search(embeddings_array, k=min(len(embeddings), 5))

    # Create mapping using similarity scores
    mapping = {}
    for i, (node, sim_scores, idx_list) in enumerate(
        zip(original_nodes, similarities, indices)
    ):
        original_label = node["label"]

        # Find most similar deduped node above threshold
        # Note: After L2 normalization, similarities will be in [-1, 1]
        # with 1 being most similar (parallel vectors)
        mapped = False
        for j, sim in zip(idx_list, sim_scores):
            if j != i and sim >= threshold:  # Skip self-matches
                target_idx = min(j, len(deduped_nodes) - 1)
                mapping[original_label] = deduped_nodes[target_idx]["label"]
                mapped = True
                break

        # If no similar nodes found above threshold, map to self
        if not mapped:
            mapping[original_label] = original_label

    return mapping


def merge_similar_nodes(
    nodes: List[Dict[str, str]],
    embeddings: List[List[float]],
    threshold: float = DEFAULT_THRESHOLD,
) -> List[Dict[str, str]]:
    """
    Merges similar nodes based on cosine similarity of their embeddings.
    Returns deduplicated list of nodes with frequency information added.
    """
    if not nodes or not embeddings:
        return nodes

    # Convert embeddings to numpy array
    embeddings_array = np.array(embeddings, dtype=np.float32)

    # L2 normalize embeddings
    faiss.normalize_L2(embeddings_array)

    # Create FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_array)

    # Search for similar nodes
    similarities, indices = index.search(embeddings_array, k=len(embeddings))

    # Track merged nodes and their frequencies
    merged = {}
    frequencies = {}

    for i, (sim_scores, idx_list) in enumerate(zip(similarities, indices)):
        if i in merged:
            continue

        # Find similar nodes above threshold (skip self-matches)
        similar_indices = [
            j
            for j, sim in zip(idx_list, sim_scores)
            if j > i and sim >= threshold and j not in merged
        ]

        if similar_indices:
            merged.update({j: i for j in similar_indices})
            frequencies[i] = len(similar_indices) + 1

    # Create deduplicated list
    result = []
    for i, node in enumerate(nodes):
        if i in merged:
            continue

        new_node = node.copy()
        if i in frequencies:
            new_node[
                "description"
            ] = f"{node['description']} (repeated {frequencies[i]} times)"
        result.append(new_node)

    return result


def adjust_causal_relationships(
    relationships: List[Dict[str, str]], old_to_new_labels: Dict[str, str]
) -> List[Dict[str, str]]:
    result = []
    seen = set()

    for rel in relationships:
        if "source" not in rel or "target" not in rel:
            continue

        # Map the source and target to their new labels if they exist in old_to_new_labels
        source = old_to_new_labels.get(rel["source"], rel["source"])
        target = old_to_new_labels.get(rel["target"], rel["target"])

        # Skip self-loops but keep all other valid relationships
        if source != target:
            key = f"{source}->{target}"
            if key not in seen:
                new_rel = {"source": source, "target": target}
                result.append(new_rel)
                seen.add(key)

    return result


@asset(
    partitions_def=user_partitions_def,
    ins={
        "node_embeddings": AssetIn(
            key=["node_embeddings"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def deduplicated_graph_raw(
    context: AssetExecutionContext,
    node_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    logger = get_logger(context)

    # Collect all nodes and embeddings globally
    all_observables = []
    all_inferrables = []
    all_observable_embeddings = []
    all_inferrable_embeddings = []

    for row in node_embeddings.iter_rows(named=True):
        all_observables.extend(row["observables"])
        all_inferrables.extend(row["inferrables"])
        all_observable_embeddings.extend(row["observables_embeddings"])
        all_inferrable_embeddings.extend(row["inferrables_embeddings"])

    # Perform global deduplication
    deduped_observables = merge_similar_nodes(
        all_observables, all_observable_embeddings
    )
    deduped_inferrables = merge_similar_nodes(
        all_inferrables, all_inferrable_embeddings
    )

    # Create comprehensive mappings using similarity-based approach
    observable_mapping = create_node_mapping(
        all_observables, deduped_observables, all_observable_embeddings
    )
    inferrable_mapping = create_node_mapping(
        all_inferrables, deduped_inferrables, all_inferrable_embeddings
    )

    # Combine mappings
    global_old_to_new = {**observable_mapping, **inferrable_mapping}

    # Process each row with the global mapping
    processed_relationships = []
    for row in node_embeddings.iter_rows(named=True):
        adjusted_relationships = adjust_causal_relationships(
            row["causal_relationships"], global_old_to_new
        )
        processed_relationships.append(adjusted_relationships)

    # Create the result DataFrame
    result = node_embeddings.with_columns(
        [
            pl.Series("observables", [deduped_observables] * len(node_embeddings)),
            pl.Series("inferrables", [deduped_inferrables] * len(node_embeddings)),
            pl.Series("causal_relationships", processed_relationships),
        ]
    )

    logger.info(f"Processed {len(result)} conversations")
    return result
