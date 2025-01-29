from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json
from toolz import concat, groupby, merge_with

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


def _merge_dict_lists(list1: list[dict], list2: list[dict] | None) -> list[dict]:
    if list2 is None:
        return list1

    lookup1 = {item["id"]: item for item in list1}
    lookup2 = {item["id"]: item for item in list2}
    common_ids = set(lookup1.keys()) & set(lookup2.keys())

    def combine_values(values):
        if isinstance(values[0], list):
            return values[0] + values[1]
        # Take first non-null value
        return next((v for v in values if v is not None), None)

    result = []
    for id_ in common_ids:
        merged = merge_with(combine_values, lookup1[id_], lookup2[id_])
        result.append(merged)

    return result


def _get_cross_chunk_causality_prompt_sequence(
    chunk_subgraph: list[dict], prev_chunk_subgraph: list[dict]
) -> PromptSequence:
    return [
        dedent(
            f"""
            You will be given two causal graphs belonging to two subsequent chunks of a conversation between two people.
            The two causal graphs have been contructed separately, so we need to find any missing causal relationships
            between the two graphs.

            Provide your answer as a list of node_labels for the current chunk with "caused_by" and "caused" arrays of node_labels from the previous chunk.
            "caused_by" should contain the node_labels that are likely to have caused the current node_label.
            "caused" should contain the node_labels that are likely to have been caused by the current node_label.

            Use this format:
            [
              {{
                "current_id": "current_node_label",
                "caused_by": ["prev_node_label", ...],
                "caused": ["prev_node_label", ...]
              }},
              ...
            ]
            If you believe there are no missing causal links between the two graphs, return an empty list.

            The causal graph for the previous chunk is:
            {prev_chunk_subgraph}

            The causal graph for the current chunk is:
            {chunk_subgraph}
            """
        ).strip(),
    ]


def _parse_cross_chunk_causality_response(response: str) -> list[dict] | None:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, list):
            return res
        else:
            return None
    except Exception:
        return None


class WhatsappCrossChunkCausalityConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "whatsapp_chunks_subgraphs": AssetIn(
            key=["whatsapp_chunks_subgraphs"],
        ),
    },
)
def whatsapp_cross_chunk_causality(
    context: AssetExecutionContext,
    whatsapp_chunks_subgraphs: pl.DataFrame,
    llama70b: BaseLlmResource,
    config: WhatsappCrossChunkCausalityConfig,
) -> pl.DataFrame:
    """
    Determine the causality between chunks.
    """

    df = (
        whatsapp_chunks_subgraphs.with_columns(
            combined_subgraph=pl.concat_list(
                ["subgraph_attributes", "subgraph_context", "subgraph_meta"]
            )
        )
        .sort("chunk_id")
        .slice(0, config.row_limit)
    )

    # Get comparions pairs for each chunk based on these constraints:
    max_time_range = pl.duration(days=3)
    min_comparisons = 1
    max_comparisons = 3

    # Result schema: chunk_id, combined_subgraph, picked: {prev_chunk_id, prev_end_dt, prev_combined_subgraph, rank}
    df_pairs = (
        df.lazy()
        # 1) Cross-join with itself, renaming the "previous" side
        .join(
            df.lazy().select(
                [
                    pl.col("chunk_id").alias("prev_chunk_id"),
                    pl.col("end_dt").alias("prev_end_dt"),
                    pl.col("combined_subgraph").alias("prev_combined_subgraph"),
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
                        pl.col("prev_combined_subgraph"),
                    ]
                )
                # We sort them by ascending rank to get them in “most recent first” order
                .sort_by("rank")
                .alias("picked"),
                pl.col("combined_subgraph"),
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
                        row["combined_subgraph"], pick["prev_combined_subgraph"]
                    ),
                )
            )

    completions, cost = llama70b.get_prompt_sequences_completions_batch(
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
        k: list(concat(v for v in vals if v is not None))
        for k, vals in groupby(lambda x: x[0], chunk_id_new_causal_links).items()
    }

    # For each chunk_id, merge the new causal links with the existing ones
    return df.with_columns(
        pl.struct(["chunk_id", "combined_subgraph"])
        .map_elements(
            lambda x: _merge_dict_lists(
                x["combined_subgraph"], chunk_id_to_new_causal_links.get(x["chunk_id"])
            )
        )
        .alias("combined_subgraph")
    )
