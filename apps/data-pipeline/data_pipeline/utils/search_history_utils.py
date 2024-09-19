import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple

import polars as pl
from dagster import get_dagster_logger
from json_repair import repair_json

from data_pipeline.resources.llm_inference.local.local_llm_resource import (
    LocalLlmResource,
)


@dataclass
class FullHistorySessionsOutput:
    output_df: pl.DataFrame
    count_invalid_interests: int
    count_invalid_quirkiness: int


def generate_chunks(daily_dfs: Dict[datetime.date, pl.DataFrame], chunk_size: int = 15):
    chunks: Dict[datetime.date, List[pl.DataFrame]] = {}

    for date, day_df in daily_dfs.items():
        chunks[date] = []
        for slice in day_df.iter_slices(chunk_size):
            chunks[date].append(slice.select("hour", "title"))

    return chunks


# Extract two lists from the text
def extract_interests_lists(text: str) -> Tuple[List[str], List[str]]:
    try:
        j = repair_json(text, return_objects=True)

        if isinstance(j, dict):
            return j.get("interests", []), j.get("quirky_interests", [])
        else:
            return [], []
    except Exception:
        return [], []


def generate_chunked_interests(
    local_llm: LocalLlmResource,
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

    results, _ = local_llm.get_prompt_sequences_completions_batch(prompt_sequences)

    chunked_interests_normal, chunked_interests_quirky, raw_results = zip(
        *[
            (*extract_interests_lists(res[-1]), res) if res else ([], [], [])
            for res in results
        ]
    )

    # Merge two lists into one
    chunked_interests = [
        [
            *chunked_interests_normal[i],
            *chunked_interests_quirky[i],
        ]
        for i in range(len(chunked_interests_normal))
    ]

    # Add a boolean list to indicate if the interest is quirky
    chunked_interests_quirkiness = []
    for i in range(len(chunked_interests)):
        chunked_interests_quirkiness.append(
            [False] * len(chunked_interests_normal[i])
            + [True] * len(chunked_interests_quirky[i])
        )

    for date, interests, raw_interest, quirkyness, raw_result in zip(
        dates,
        chunked_interests,
        raw_interests,
        chunked_interests_quirkiness,
        raw_results,
    ):
        yield {
            "date": date,
            "interests": interests,
            "interests_quirkiness": quirkyness,
            "count_invalid_interests": int(not interests),
            "count_invalid_quirkiness": int(not quirkyness),
            "raw_interests": raw_interest,
            "raw_results": raw_result,
        }


def get_full_history_sessions(
    full_takeout: pl.DataFrame,
    chunk_size: int,
    prompt_sequence: List[str],
    local_llm: LocalLlmResource,
) -> FullHistorySessionsOutput:
    daily_dfs = full_takeout.with_columns(
        date=pl.col("timestamp").dt.date()
    ).partition_by("date", as_dict=True, include_key=False)

    logger = get_dagster_logger()
    logger.info(f"Processing {len(daily_dfs)} records")

    chunks = generate_chunks(daily_dfs, chunk_size)
    daily_records = generate_chunked_interests(local_llm, chunks, prompt_sequence)

    grouped_df = (
        pl.DataFrame(daily_records)
        .group_by("date")
        .agg(
            [
                pl.col("interests").flatten(),
                pl.col("interests_quirkiness").flatten(),
                pl.col("raw_interests").flatten(),
                pl.col("raw_results").flatten(),
                pl.col("count_invalid_interests").sum(),
                pl.col("count_invalid_quirkiness").sum(),
            ]
        )
    )

    return FullHistorySessionsOutput(
        output_df=grouped_df.select(
            "date", "interests", "interests_quirkiness", "raw_interests", "raw_results"
        ),
        count_invalid_interests=int(grouped_df["count_invalid_interests"].sum()),
        count_invalid_quirkiness=int(grouped_df["count_invalid_quirkiness"].sum()),
    )
