from typing import Dict, List, Optional, Set, Tuple

import faiss
import numpy as np
import polars as pl


def _find_similar_nodes(
    embeddings: List[List[float]],
    threshold: float,
    max_k: Optional[int] = None,
) -> List[Tuple[int, List[Tuple[int, float]]]]:
    """
    Performs a FAISS similarity search and returns all similar node pairs
    that exceed the `threshold`.

    Args:
        embeddings: A list of embedding vectors (one per node).
        threshold: Cosine similarity threshold for considering two nodes 'similar'.

    Returns:
        A list of tuples, where each tuple is:
            (node_index, [(similar_node_index, similarity_score), ...])
    """
    if not embeddings:
        return []

    embeddings_array = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings_array)

    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_array)  # type: ignore

    similarities, indices = index.search(embeddings_array, k=(max_k or len(embeddings)))  # type: ignore

    # Collect similar pairs
    similar_pairs = []
    for i, (sim_scores, idx_list) in enumerate(zip(similarities, indices)):
        matches = []
        for j, sim in zip(idx_list, sim_scores):
            if i != j and sim >= threshold:
                matches.append((j, float(sim)))
        similar_pairs.append((i, matches))

    return similar_pairs


def _build_merge_groups(
    similar_pairs: List[Tuple[int, List[Tuple[int, float]]]],
    nodes: List[Dict[str, str]],
    label_col: str,
) -> List[Set[str]]:
    """
    Builds groups of node labels (strings) that should be merged together,
    using a Union-Find structure for transitivity.

    Args:
        similar_pairs: Output of `find_similar_nodes`.
        nodes: A list of dicts, each dict representing a node's attributes.
        label_col: The key in the node dict that represents the node's unique label.

    Returns:
        A list of sets. Each set is a group of labels that should be merged.
    """
    # Initialize Union-Find
    parent = {node[label_col]: node[label_col] for node in nodes}
    rank = {node[label_col]: 0 for node in nodes}

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

    # For each pair, union their labels
    for idx, matches in similar_pairs:
        node_label = nodes[idx][label_col]
        for match_idx, _sim in matches:
            match_label = nodes[match_idx][label_col]
            union(node_label, match_label)

    # Collect final groups
    groups_map = {}
    for node in nodes:
        root = find(node[label_col])
        if root not in groups_map:
            groups_map[root] = set()
        groups_map[root].add(node[label_col])

    return list(groups_map.values())


def _merge_nodes(
    nodes: List[Dict[str, str]],
    merge_groups: List[Set[str]],
    single_fields: List[str],
    list_fields: List[Tuple[str, str]],
    label_col: str,
) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """
    Merges node attributes based on the provided merge groups.

    Args:
        nodes: List of dicts, each representing a node's attributes.
        merge_groups: A list of sets of labels, where each set is to be merged.
        single_fields: Which fields get retained as single values (taken from the
            first node in the merge group).
        list_fields: Which fields get aggregated into a list. Each element in `list_fields`
            is a tuple (new_field_name, old_field_name).
        label_col: The name of the label (unique ID) in each node dict.

    Returns:
        A tuple of:
          (1) A list of merged node dicts
          (2) A label mapping dict from old_label -> new_label (the representative).
    """
    # Create mapping from old labels to their representative
    label_mapping = {}
    for group in merge_groups:
        # pick a stable representative; in this example, we pick min() by alphabetical
        representative = min(group)
        for label in group:
            label_mapping[label] = representative

    # If a label wasn't in any merge group, map it to itself
    for node in nodes:
        node_label = node[label_col]
        if node_label not in label_mapping:
            label_mapping[node_label] = node_label

    merged_nodes = {}
    for node in nodes:
        old_label = node[label_col]
        new_label = label_mapping[old_label]

        if new_label not in merged_nodes:
            merged_nodes[new_label] = {}
            # Force the "label_col" for the merged node to be the representative
            merged_nodes[new_label][label_col] = new_label
            # Initialize frequency counter
            merged_nodes[new_label]["frequency"] = 1

            # Copy over single-value fields from the first example node
            for field in single_fields:
                if field == label_col:
                    continue  # we already set that
                merged_nodes[new_label][field] = node.get(field, None)

            # Initialize list-value fields
            for new_field_name, old_field_name in list_fields:
                merged_nodes[new_label][new_field_name] = [
                    node.get(old_field_name, None)
                ]

        else:
            # We are merging into an existing representative
            merged_nodes[new_label]["frequency"] += 1
            for new_field_name, old_field_name in list_fields:
                merged_nodes[new_label][new_field_name].append(
                    node.get(old_field_name, None)
                )

    return list(merged_nodes.values()), label_mapping


def deduplicate_nodes_dataframe(
    df: pl.DataFrame,
    label_col: str,
    embedding_col: str,
    single_fields: List[str],
    list_fields: List[Tuple[str, str]],
    relationship_col: str,
    threshold: float = 0.9,
    max_k: Optional[int] = None,
) -> pl.DataFrame:
    """
    High-level pipeline that:
      1) Extracts embeddings,
      2) Finds similar node groups,
      3) Merges them,
      4) (Optionally) merges relationships,
      5) Returns a deduplicated DataFrame and final relationship list.

    Args:
        df: Your input Polars DataFrame containing the nodes.
        label_col: Name of the column containing the unique node label (string ID).
        embedding_col: Name of the column containing the node embeddings (List[float]).
        single_fields: Fields to treat as single-valued in merges.
        list_fields: Fields to treat as aggregated lists in merges.
                     Each item is (new_field_name, old_field_name).
        relationship_col: If present, the column containing relationships to deduplicate
                          and re-map. Typically a list of dicts with "source" and "target".
        threshold: Cosine similarity threshold for merging nodes.
        max_k: Max # of neighbors to check in FAISS. (Optional, defaults to len(embeddings))

    Returns:
        A Polars DataFrame of merged nodes
    """
    # STEP 1: Find similar nodes
    embeddings = df[embedding_col].to_list()
    # If you want to override k, you can modify find_similar_nodes or pass it in
    similar_pairs = _find_similar_nodes(embeddings, threshold, max_k)

    # STEP 2: Build merge groups
    # We'll ensure we include label_col plus the single and list fields
    fields_to_select = set([label_col] + single_fields + [lf[1] for lf in list_fields])
    partial_df = df.select(list(fields_to_select)).to_dicts()  # List[Dict]
    merge_groups = _build_merge_groups(similar_pairs, partial_df, label_col=label_col)

    # STEP 3: Merge nodes
    merged_nodes_list, label_mapping = _merge_nodes(
        partial_df,
        merge_groups,
        single_fields,
        list_fields,
        label_col=label_col,
    )

    # STEP 4: Deduplicate relationships if desired
    final_relationships = []
    if relationship_col and (relationship_col in df.columns):
        relationships = df[relationship_col].explode().drop_nulls().to_list()
        seen_relationships = set()
        for rel in relationships:
            old_source = rel.get("source")
            old_target = rel.get("target")
            if not old_source or not old_target:
                continue

            new_source = label_mapping.get(old_source, old_source)
            new_target = label_mapping.get(old_target, old_target)

            # Avoid self-loops, or duplicates
            if new_source != new_target:
                rel_key = f"{new_source}->{new_target}"
                if rel_key not in seen_relationships:
                    seen_relationships.add(rel_key)
                    final_relationships.append(
                        {"source": new_source, "target": new_target}
                    )

    # STEP 5: Convert merged node dicts into a Polars DataFrame
    # Optionally, you can add 'frequency', edges, or other logic here
    merged_rows = []
    # Build adjacency list from final_relationships
    node_edges_map: Dict[str, List[str]] = {}
    for r in final_relationships:
        s, t = r["source"], r["target"]
        node_edges_map.setdefault(s, [])
        if t not in node_edges_map[s]:
            node_edges_map[s].append(t)

    for node_dict in merged_nodes_list:
        row = {}
        # Single value fields
        for field in single_fields:
            row[field] = node_dict.get(field, None)

        # Aggregated list-value fields
        for new_field_name, _old_field_name in list_fields:
            row[new_field_name] = node_dict.get(new_field_name, [])

        # The label and frequency
        row[label_col] = node_dict.get(label_col, None)
        row["frequency"] = node_dict.get("frequency", 1)

        # Edges for the adjacency list
        label_val = node_dict.get(label_col, None)
        if label_val:
            row["edges"] = node_edges_map.get(label_val, [])

        merged_rows.append(row)

    merged_df = pl.DataFrame(merged_rows)

    # Assign relationships from the adjacency list to the row where the node is a source
    if final_relationships:
        merged_df = merged_df.join(
            pl.DataFrame(final_relationships)
            .group_by("source")
            .agg(pl.struct(["source", "target"]).alias("relationships")),
            left_on="id",
            right_on="source",
            how="left",
        ).with_columns(pl.col("relationships").fill_null(pl.Series([[]])))

    return merged_df
