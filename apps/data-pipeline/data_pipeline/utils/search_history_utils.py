import datetime
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import polars as pl
from dagster import get_dagster_logger
from json_repair import repair_json

from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource


@dataclass
class FullHistorySessionsOutput:
    output_df: pl.DataFrame
    count_invalid_interests: int


def generate_chunks(daily_dfs: Dict[datetime.date, pl.DataFrame], chunk_size: int = 15):
    chunks: Dict[datetime.date, List[pl.DataFrame]] = {}

    for date, day_df in daily_dfs.items():
        chunks[date] = []
        for slice in day_df.iter_slices(chunk_size):
            chunks[date].append(slice.select("hour", "title"))

    return chunks


# Extract two lists from the text
def extract_interests_lists(text: str) -> List[str]:
    try:
        j = repair_json(text, return_objects=True)

        res = j if isinstance(j, list) else []
    except Exception:
        res = []

    try:
        return np.hstack(res).tolist()
    except Exception:
        return []


def generate_chunked_interests(
    llm_resource: BaseLlmResource,
    chunks: Dict[datetime.date, List[pl.DataFrame]],
    prompt_sequence_base: List[str],
):
    dates, prompt_sequences, raw_interests = zip(
        *[
            (
                date,
                [f"{prompt_sequence_base[0]}\n{frame}", *prompt_sequence_base[1:]],
                frame["title"].to_list(),
            )
            for date, day_dfs in chunks.items()
            for frame in day_dfs
        ]
    )

    results, cost = llm_resource.get_prompt_sequences_completions_batch(
        prompt_sequences
    )
    get_dagster_logger().info(f"Execution cost: ${cost:.2f}")

    chunked_interests, raw_results = zip(
        *[
            (*extract_interests_lists(res[-1]), res) if res else ([], [])
            for res in results
        ]
    )

    for date, interest, raw_interest, raw_result in zip(
        dates,
        chunked_interests,
        raw_interests,
        raw_results,
    ):
        yield {
            "date": date,
            "interests": interest,
            "count_invalid_interests": int(not interest),
            "raw_interests": raw_interest,
            "raw_results": raw_result,
        }


def get_full_history_sessions(
    full_takeout: pl.DataFrame,
    chunk_size: int,
    prompt_sequence: List[str],
    llm_resource: BaseLlmResource,
) -> FullHistorySessionsOutput:
    daily_dfs = full_takeout.with_columns(
        date=pl.col("timestamp").dt.date()
    ).partition_by("date", as_dict=True, include_key=False)

    logger = get_dagster_logger()
    logger.info(f"Processing {len(daily_dfs)} days")

    chunks = generate_chunks(daily_dfs, chunk_size)
    daily_records = generate_chunked_interests(llm_resource, chunks, prompt_sequence)

    grouped_df = (
        pl.DataFrame(daily_records, strict=False)
        .group_by("date")
        .agg(
            [
                pl.col("interests").flatten(),
                pl.col("raw_interests").flatten(),
                pl.col("raw_results").flatten(),
                pl.col("count_invalid_interests").sum(),
            ]
        )
    )

    return FullHistorySessionsOutput(
        output_df=grouped_df.select(
            "date", "interests", "raw_interests", "raw_results"
        ),
        count_invalid_interests=int(grouped_df["count_invalid_interests"].sum()),
    )
