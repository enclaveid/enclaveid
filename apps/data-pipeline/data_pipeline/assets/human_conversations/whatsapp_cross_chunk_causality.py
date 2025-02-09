from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json
from toolz import concat, groupby, merge_with

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import multi_phone_number_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


def _get_only_nodes_without_causes(subgraph: list[dict]) -> list[dict]:
    # Get all node IDs that appear in any "caused" array
    caused_ids = set()
    for node in subgraph:
        if "caused" in node:
            caused_ids.update(node["caused"])

    # Only keep nodes that don't have explicit caused_by relationships or appear in others' caused arrays
    return [
        node
        for node in subgraph
        if (len(node.get("caused_by", [])) == 0) and (node["id"] not in caused_ids)
    ]


# TODO: do in polars
def _merge_dict_lists(list1, list2):
    if not list2:
        return list1

    # Create lookup for the right side list
    lookup2 = {item["id"]: item for item in list2}

    def combine_values(values):
        if isinstance(values[0], list):
            # If we have a matching item from list2, concatenate
            return values[0] + values[1] if len(values) > 1 else values[0]
        # Take first non-null value
        return next((v for v in values if v is not None), None)

    result = []
    # Iterate through all items in list1
    for item1 in list1:
        id_ = item1["id"]
        # Get matching item from list2 if it exists
        if id_ in lookup2:
            merged = merge_with(combine_values, item1, lookup2[id_])
        else:
            merged = item1  # Keep original item if no match
        result.append(merged)

    return result


def _get_cross_chunk_causality_prompt_sequence(
    chunk_subgraph: list[dict], prev_chunk_subgraph: list[dict]
) -> PromptSequence:
    return [
        dedent(
            f"""
            You will be given two sets of nodes belonging to two subsequent chunks of a conversation between two people.
            The two sets have been analyzed separately, so we need to find any missing causal relationships between them.

            Provide your answer as a list of node_labels (for the current chunk) with "caused_by" and "caused" arrays of node_labels (from the previous chunk).
            "caused_by" should contain the node_labels that are likely to HAVE CAUSED the current node_label.
            "caused" should contain the node_labels that are likely to HAVE BEEN CAUSED BY the current node_label.

            Use this format:
            [
              {{
                "id": "current_node_label",
                "caused_by": ["prev_node_label", ...],
                "caused": ["prev_node_label", ...]
              }},
              ...
            ]
            If you believe there are no missing causal links between the two sets, return an empty list.

            The causal graph for the previous chunk is:
            {prev_chunk_subgraph}

            The nodes of the current chunk are:
            {chunk_subgraph}
            """
        ).strip(),
    ]


def _parse_cross_chunk_causality_response(response: str) -> list[dict] | None:
    try:
        res = repair_json(response, return_objects=True)

        # Do some validation
        required_keys = {"id", "caused_by", "caused"}
        if (
            isinstance(res, list)
            and all(isinstance(x, dict) for x in res)
            and all(required_keys.issubset(x.keys()) for x in res)
            and all(isinstance(x["caused_by"], list) for x in res)
            and all(isinstance(x["caused"], list) for x in res)
        ):
            return res
        else:
            return None
    except Exception:
        return None


class WhatsappCrossChunkCausalityConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None


@asset(
    partitions_def=multi_phone_number_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_subgraphs_sanitized": AssetIn(
            key=["whatsapp_subgraphs_sanitized"],
        ),
    },
)
def whatsapp_cross_chunk_causality(
    context: AssetExecutionContext,
    whatsapp_subgraphs_sanitized: pl.DataFrame,
    llama70b: BaseLlmResource,
    config: WhatsappCrossChunkCausalityConfig,
) -> pl.DataFrame:
    """
    Determine the causality between chunks.
    """
    llm = llama70b
    df = whatsapp_subgraphs_sanitized.sort("chunk_id").slice(0, config.row_limit)

    # Get comparions pairs for each chunk based on these constraints:
    max_time_range = pl.duration(days=7)
    min_comparisons = 1
    max_comparisons = 10

    # Result schema: chunk_id, subgraph_combined, picked: {prev_chunk_id, prev_end_dt, prev_subgraph_combined, rank}
    df_pairs = (
        df.lazy()
        # 1) Cross-join with itself, renaming the "previous" side
        .join(
            df.lazy().select(
                [
                    pl.col("chunk_id").alias("prev_chunk_id"),
                    pl.col("end_dt").alias("prev_end_dt"),
                    pl.col("subgraph_combined").alias("prev_subgraph_combined"),
                ]
            ),
            how="cross",
        )
        # Keep only rows where the "previous" chunk has a smaller ID
        .filter(pl.col("chunk_id") > pl.col("prev_chunk_id"))
        # 2) Compute time difference = start_dt(current) - end_dt(previous)
        .with_columns((pl.col("start_dt") - pl.col("prev_end_dt")).alias("time_diff"))
        # 3) Within each current chunk_id, define a rank based on recency.
        #    Let's assume "most recent" means largest `prev_end_dt`, so use descending=True.
        .with_columns(
            pl.col("prev_end_dt")
            .rank(method="ordinal", descending=True)
            .over("chunk_id")
            .alias("rank")
        )
        # 4) Now filter to keep only:
        #    - rank <= min_comparisons (always)
        #    - OR (rank <= max_comparisons AND time_diff <= max_time_range)
        .filter(
            (pl.col("rank") <= min_comparisons)
            | (
                (pl.col("rank") <= max_comparisons)
                & (pl.col("time_diff") <= max_time_range)
            )
        )
        .group_by("chunk_id")
        .agg(
            [
                pl.struct(
                    [
                        pl.col("prev_chunk_id"),
                        pl.col("prev_end_dt"),
                        pl.col("rank"),
                        pl.col("prev_subgraph_combined"),
                    ]
                )
                # We sort them by ascending rank to get them in "most recent first" order
                .sort_by("rank")
                .alias("picked"),
                pl.col("subgraph_combined").flatten(),
            ]
        )
        .collect()
        .sort("chunk_id")
    )

    chunk_id_prompt_sequences: list[tuple[int, PromptSequence]] = []
    for row in df_pairs.iter_rows(named=True):
        for pick in row["picked"]:
            chunk_id_prompt_sequences.append(
                (
                    row["chunk_id"],
                    _get_cross_chunk_causality_prompt_sequence(
                        _get_only_nodes_without_causes(
                            row["subgraph_combined"]
                        ),  # For the current chunk, only submit nodes with degree 0
                        pick["prev_subgraph_combined"],
                    ),
                )
            )

    completions, cost = llm.get_prompt_sequences_completions_batch(
        [x[1] for x in chunk_id_prompt_sequences]
    )

    context.log.info(f"Total cost: ${cost:.2f}")

    chunk_id_new_causal_links = [
        (chunk_id, _parse_cross_chunk_causality_response(completion[-1]))
        if completion
        else (chunk_id, [])
        for completion, (chunk_id, _) in zip(completions, chunk_id_prompt_sequences)
    ]

    chunk_id_to_new_causal_links = {
        k: list(concat(v[1] for v in vals if v[1] is not None))
        for k, vals in groupby(lambda x: x[0], chunk_id_new_causal_links).items()
    }

    # For each chunk_id, merge the new causal links with the existing ones
    return df.with_columns(
        subgraph_combined=pl.struct(["chunk_id", "subgraph_combined"]).map_elements(
            lambda x: _merge_dict_lists(
                x["subgraph_combined"], chunk_id_to_new_causal_links.get(x["chunk_id"])
            )
        ),
        new_causal_links=pl.col("chunk_id").map_elements(
            lambda x: chunk_id_to_new_causal_links.get(x, [])
        ),
    )
