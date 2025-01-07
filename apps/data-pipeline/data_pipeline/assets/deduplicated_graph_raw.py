from typing import Dict, List, Set, Tuple

import faiss
import numpy as np
import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from pydantic import Field

from data_pipeline.partitions import user_partitions_def

# Which fields remain single vs. which are aggregated
SINGLE_VALUE_FIELDS = [
    "label",
    "description",
    "node_type",
    "embedding",
    "conversation_id",
    "cluster_label",
    "category",
    "is_personal",
]
LIST_VALUE_FIELDS = [
    ("merged_labels", "label"),
    ("merged_descriptions", "description"),
    ("dates", "date"),
    ("times", "time"),
]


def find_similar_nodes(
    embeddings: List[List[float]], threshold: float
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

    # Process results to find all similar pairs
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
        for match_idx, _ in matches:
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
    nodes: List[Dict[str, str]],
    merge_groups: List[Set[str]],
    single_fields: List[str],
    list_fields: List[Tuple[str, str]],
) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """
    Merges nodes based on merge groups and returns merged nodes and label mapping.
    """
    # Create mapping from old to new labels
    label_mapping = {}
    for group in merge_groups:
        representative = min(group)  # e.g., alphabetical
        for label in group:
            label_mapping[label] = representative

    # Handle nodes not in any group
    for node in nodes:
        if node["label"] not in label_mapping:
            label_mapping[node["label"]] = node["label"]

    merged_nodes = {}
    for node in nodes:
        old_label = node["label"]
        new_label = label_mapping[old_label]

        if new_label not in merged_nodes:
            merged_nodes[new_label] = {}

            # Force the "label" of the merged node to be the new_label
            merged_nodes[new_label]["label"] = new_label

            # Copy over single-value fields
            for field in single_fields:
                if field == "label":
                    continue  # already handled
                merged_nodes[new_label][field] = node.get(field, "unknown")

            # Initialize list-value fields
            for new_field_name, old_field_name in list_fields:
                merged_nodes[new_label][new_field_name] = [
                    node.get(old_field_name, None)
                ]
        else:
            # Node already exists; just add to the aggregated lists
            for new_field_name, old_field_name in list_fields:
                merged_nodes[new_label][new_field_name].append(
                    node.get(old_field_name, None)
                )

    return list(merged_nodes.values()), label_mapping


class DeduplicatedGraphRawConfig(Config):
    threshold: float = Field(
        default=0.9, description="Cosine similarity threshold for merging nodes"
    )


@asset(
    partitions_def=user_partitions_def,
    ins={"node_embeddings": AssetIn(key=["node_embeddings"])},
    io_manager_key="parquet_io_manager",
)
def deduplicated_graph_raw(
    context: AssetExecutionContext,
    config: DeduplicatedGraphRawConfig,
    node_embeddings: pl.DataFrame,
) -> pl.DataFrame:
    df = node_embeddings

    # 1. Find similar nodes
    similarities = find_similar_nodes(df["embedding"].to_list(), config.threshold)

    # 2. Build merge groups
    fields_to_select = set(SINGLE_VALUE_FIELDS + [lf[1] for lf in LIST_VALUE_FIELDS])
    partial_df = df.select(list(fields_to_select)).to_dicts()
    merge_groups = build_merge_groups(similarities, partial_df)

    # 3. Merge nodes
    merged_nodes, mapping = merge_nodes(
        partial_df,
        merge_groups,
        SINGLE_VALUE_FIELDS,
        LIST_VALUE_FIELDS,
    )

    # 4. Build causal relationships (if present)
    final_relationships = []
    seen_relationships = set()

    if "causal_relationships" in df.columns:
        for rel in df["causal_relationships"].explode().drop_nulls().to_list():
            new_source = mapping.get(rel["source"], rel["source"])
            new_target = mapping.get(rel["target"], rel["target"])

            # Avoid self-loops
            if new_source != new_target:
                rel_key = f"{new_source}->{new_target}"
                if rel_key not in seen_relationships:
                    final_relationships.append(
                        {"source": new_source, "target": new_target}
                    )
                    seen_relationships.add(rel_key)

    # Create adjacency list
    node_edges: Dict[str, List[str]] = {}
    for rel in final_relationships:
        source, target = rel["source"], rel["target"]
        node_edges.setdefault(source, [])
        if target not in node_edges[source]:
            node_edges[source].append(target)

    # 5. Build the final DataFrame using SINGLE_VALUE_FIELDS and LIST_VALUE_FIELDS
    rows_for_pl = []
    for node in merged_nodes:
        row = {}

        # Single-value fields
        for field in SINGLE_VALUE_FIELDS:
            row[field] = node[field]

        # Aggregated list-value fields
        for new_field_name, _old_field_name in LIST_VALUE_FIELDS:
            row[new_field_name] = node[new_field_name]

        # Additional derived fields
        row["frequency"] = len(node["merged_labels"])
        row["edges"] = node_edges.get(node["label"], [])

        rows_for_pl.append(row)

    # Convert to DataFrame
    result = pl.DataFrame(rows_for_pl).with_columns(
        start_date=pl.col("dates").list.first(),
        end_date=pl.col("dates").list.last(),
        start_time=pl.col("times").list.first(),
        end_time=pl.col("times").list.last(),
    )

    context.log.info(f"Processed {len(result)} nodes")

    return result
