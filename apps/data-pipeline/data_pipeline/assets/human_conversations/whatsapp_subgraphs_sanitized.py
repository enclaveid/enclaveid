import re
from collections import defaultdict

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset

from data_pipeline.partitions import multi_phone_number_partitions_def


def _sanitize_to_snake_case(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def extract_ids_in_row(row: dict) -> set[str]:
    """
    Given a dict with keys ["subgraph_attributes", "subgraph_context", "subgraph_meta"],
    gather all 'id' plus 'caused_by'/'caused' references in that row.
    """
    out = set()
    for col in ["subgraph_attributes", "subgraph_context", "subgraph_meta"]:
        nodes = row.get(col, [])
        if not nodes:
            continue
        for node in nodes:
            if not node:
                continue
            if "id" in node and node["id"]:
                out.add(node["id"])
            for ref_col in ["caused_by", "caused"]:
                if ref_col in node and node[ref_col]:
                    out.update(node[ref_col])
    return out


def build_row_id_map(row_id: str, original_ids: set[str]) -> dict[str, str]:
    """
    Build a row-specific map: raw ID -> (row-prefixed, snake-cased, unique) ID.
    For collisions within this row, append _2, _3, etc.
    """
    mapping = {}
    counts = defaultdict(int)

    for oid in sorted(original_ids):
        base = _sanitize_to_snake_case(oid)
        counts[base] += 1
        if counts[base] == 1:
            # e.g. "row0_abc123"
            mapping[oid] = f"{row_id}_{base}"
        else:
            # e.g. "row0_abc123_2"
            mapping[oid] = f"{row_id}_{base}_{counts[base]}"

    return mapping


def apply_row_id_map(node_list: list[dict], row_map: dict[str, str]) -> list[dict]:
    """
    Apply the row-specific ID map to each node:
        - node["id"]
        - node["caused_by"]
        - node["caused"]
    """
    if not node_list:
        return []

    out = []
    for node in node_list:
        if not node:
            out.append(node)
            continue

        new_node = node.copy()

        # Own ID
        if "id" in new_node and new_node["id"] in row_map:
            new_node["id"] = row_map[new_node["id"]]

        # caused_by / caused
        for ref_col in ["caused_by", "caused"]:
            if ref_col in new_node and new_node[ref_col]:
                new_node[ref_col] = [row_map.get(ref, ref) for ref in new_node[ref_col]]

        out.append(new_node)
    return out


def sanitize_subgraphs_for_row(row: dict) -> dict:
    """
    Given a row dict that includes "row_idx" plus the three subgraph columns,
    do row-level ID extraction, mapping, and application.
    """
    row_idx = row["row_idx"]

    # 1) extract raw IDs in this row
    raw_ids = extract_ids_in_row(row)

    # 2) build row-specific map (prefix with row_idx)
    row_map = build_row_id_map(f"row{row_idx}", raw_ids)

    # 3) apply that map to each subgraph column
    return {
        "subgraph_attributes": apply_row_id_map(row["subgraph_attributes"], row_map),
        "subgraph_context": apply_row_id_map(row["subgraph_context"], row_map),
        "subgraph_meta": apply_row_id_map(row["subgraph_meta"], row_map),
    }


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_chunks_subgraphs": AssetIn(key=["whatsapp_chunks_subgraphs"]),
    },
)
def whatsapp_subgraphs_sanitized(
    context: AssetExecutionContext,
    whatsapp_chunks_subgraphs: pl.DataFrame,
) -> pl.DataFrame:
    """
    For each row, we prepend "row<idx>_" to all sanitized IDs so that there's
    no collision across rows, while ensuring within-row consistency.
    """
    # (A) Add a 0-based row index column
    df_with_idx = whatsapp_chunks_subgraphs.with_row_count(name="row_idx")

    columns = ["subgraph_attributes", "subgraph_context", "subgraph_meta"]

    # (B) Combine relevant columns into one struct for row-level sanitization
    #     We'll apply sanitize_subgraphs_for_row, which returns a dict
    #     of subgraph_attributes/context/meta.
    sanitized = df_with_idx.with_columns(
        pl.struct(columns + ["row_idx"])
        .map_elements(sanitize_subgraphs_for_row)
        .alias("sanitized_subgraphs")
    ).drop(columns + ["row_idx"])

    # (C) unnest
    df_sanitized = sanitized.unnest("sanitized_subgraphs")

    # (D) Clean up
    df_sanitized = df_sanitized.with_columns(
        pl.concat_list(columns).alias("subgraph_combined")
    ).drop(columns)

    check_df = (
        df_sanitized.select("subgraph_combined")
        .explode("subgraph_combined")
        .unnest("subgraph_combined")
        .select("id")
    )

    context.log.info(
        f"Total ids: {check_df.count().item()}, Unique ids: {check_df.unique().count().item()}"
    )

    if check_df.count().item() != check_df.unique().count().item():
        context.log.error("Duplicate IDs in result")

    return df_sanitized
