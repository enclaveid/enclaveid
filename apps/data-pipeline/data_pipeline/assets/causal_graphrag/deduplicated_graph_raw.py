from typing import Dict, List, Set, Tuple

import faiss
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import user_partitions_def

DEFAULT_THRESHOLD = 0.9


def find_similar_nodes(
    embeddings: List[List[float]], threshold: float = DEFAULT_THRESHOLD
) -> List[Tuple[int, List[Tuple[int, float]]]]:
    """
    Performs a single FAISS similarity search and returns all similar node pairs.

    Returns:
        List of tuples containing (node_idx, [(similar_node_idx, similarity_score)])
    """
    if not embeddings:
        return []

    embeddings_array = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings_array)

    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_array)

    # Search for similar nodes
    k = min(len(embeddings), 20)
    similarities, indices = index.search(embeddings_array, k=k)

    # Process results to find all similar pairs (both directions)
    similar_pairs = []
    for i, (sim_scores, idx_list) in enumerate(zip(similarities, indices)):
        matches = []
        for j, sim in zip(idx_list, sim_scores):
            if i != j and sim >= threshold:
                matches.append((j, float(sim)))
        similar_pairs.append((i, matches))

    return similar_pairs


def build_merge_groups(
    similar_pairs: List[Tuple[int, List[Tuple[int, float]]]],
    nodes: List[Dict[str, str]],
) -> List[Set[str]]:
    """
    Builds groups of nodes that should be merged together, considering transitive relationships.
    """
    # Create initial groups using Union-Find data structure
    parent = {node["label"]: node["label"] for node in nodes}
    rank = {node["label"]: 0 for node in nodes}

    def find(x: str) -> str:
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: str, y: str):
        px, py = find(x), find(y)
        if px == py:
            return
        if rank[px] < rank[py]:
            px, py = py, px
        parent[py] = px
        if rank[px] == rank[py]:
            rank[px] += 1

    # Group similar nodes
    for idx, matches in similar_pairs:
        node_label = nodes[idx]["label"]
        for match_idx, sim in matches:
            match_label = nodes[match_idx]["label"]
            union(node_label, match_label)

    # Collect final groups
    groups = {}
    for node in nodes:
        root = find(node["label"])
        if root not in groups:
            groups[root] = set()
        groups[root].add(node["label"])

    return list(groups.values())


def merge_nodes(
    nodes: List[Dict[str, str]], merge_groups: List[Set[str]]
) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """
    Merges nodes based on merge groups and returns merged nodes and mapping.
    """
    # Create mapping from old to new labels
    label_mapping = {}
    for group in merge_groups:
        representative = min(group)  # Use consistent selection criteria
        for label in group:
            label_mapping[label] = representative

    # For nodes not in any group, map to themselves
    for node in nodes:
        if node["label"] not in label_mapping:
            label_mapping[node["label"]] = node["label"]

    # Merge nodes
    merged_nodes = {}
    for node in nodes:
        new_label = label_mapping[node["label"]]
        if new_label not in merged_nodes:
            merged_nodes[new_label] = {
                "label": new_label,
                "description": node["description"],
                "merged_nodes": [node["label"]],
                "category": node.get("category", "unknown"),
            }
        else:
            merged_nodes[new_label]["merged_nodes"].append(node["label"])

    return list(merged_nodes.values()), label_mapping


@asset(
    partitions_def=user_partitions_def,
    ins={"node_embeddings": AssetIn(key=["node_embeddings"])},
    io_manager_key="parquet_io_manager",
)
def deduplicated_graph_raw(
    context: AssetExecutionContext,
    node_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    # Collect all nodes and embeddings
    all_observables = []
    all_inferrables = []
    all_speculatives = []
    all_observable_embeddings = []
    all_inferrable_embeddings = []
    all_speculative_embeddings = []
    all_relationships = []

    for row in node_embeddings.iter_rows(named=True):
        all_observables.extend(row["observables"])
        all_inferrables.extend(row["inferrables"])
        all_speculatives.extend(row["speculatives"])
        all_observable_embeddings.extend(row["observables_embeddings"])
        all_inferrable_embeddings.extend(row["inferrables_embeddings"])
        all_speculative_embeddings.extend(row["speculatives_embeddings"])
        all_relationships.extend(row["causal_relationships"])

    # Single FAISS search for each node type
    observable_similarities = find_similar_nodes(all_observable_embeddings)
    inferrable_similarities = find_similar_nodes(all_inferrable_embeddings)
    speculative_similarities = find_similar_nodes(all_speculative_embeddings)
    # Build merge groups
    observable_groups = build_merge_groups(observable_similarities, all_observables)
    inferrable_groups = build_merge_groups(inferrable_similarities, all_inferrables)
    speculative_groups = build_merge_groups(speculative_similarities, all_speculatives)
    # Merge nodes and get mappings
    merged_observables, obs_mapping = merge_nodes(all_observables, observable_groups)
    merged_inferrables, inf_mapping = merge_nodes(all_inferrables, inferrable_groups)
    merged_speculatives, spec_mapping = merge_nodes(
        all_speculatives, speculative_groups
    )
    # Combine all nodes and mappings
    all_nodes = merged_observables + merged_inferrables + merged_speculatives
    combined_mapping = {**obs_mapping, **inf_mapping, **spec_mapping}

    # Update relationships using combined mapping
    final_relationships = []
    seen_relationships = set()

    for rel in all_relationships:
        new_source = combined_mapping.get(rel["source"], rel["source"])
        new_target = combined_mapping.get(rel["target"], rel["target"])

        if new_source != new_target:  # Avoid self-loops
            rel_key = f"{new_source}->{new_target}"
            if rel_key not in seen_relationships:
                final_relationships.append({"source": new_source, "target": new_target})
                seen_relationships.add(rel_key)

    # Build edge lists from final relationships
    node_edges = {}
    for rel in final_relationships:
        source, target = rel["source"], rel["target"]
        if source not in node_edges:
            node_edges[source] = []
        if (
            target not in node_edges[source]
        ):  # Fixed condition from target not in node_edges[target]
            node_edges[source].append(target)

    # Create final DataFrame
    result = pl.DataFrame(
        {
            "label": [node["label"] for node in all_nodes],
            "description": [node["description"] for node in all_nodes],
            "merged_nodes": [node["merged_nodes"] for node in all_nodes],
            "frequency": [len(node["merged_nodes"]) for node in all_nodes],
            "edges": [node_edges.get(node["label"], []) for node in all_nodes],
            "category": [
                "observable"
                if node["label"] in obs_mapping
                else "inferrable"
                if node["label"] in inf_mapping
                else "speculative"
                if node["label"] in spec_mapping
                else "unknown"
                for node in all_nodes
            ],
        }
    )

    context.log.info(f"Processed {len(result)} nodes")

    # label | description | merged_nodes | edges   | category
    # ------|-------------|--------------|---------|---------
    # node1 | desc1       | [node2]      | [node2] | observable
    # node2 | desc2       | [node3]      | [node3] | inferrable
    # ...
    return result
