import datetime
import re
from dataclasses import dataclass
from typing import Dict, List

import polars as pl
from dagster import get_dagster_logger
from json_repair import repair_json

from data_pipeline.resources.llm_inference.local_llm_resource import LocalLlmResource


@dataclass
class FullHistorySessionsOutput:
    output_df: pl.DataFrame
    count_invalid_interests: int
    count_invalid_uniqueness: int


def generate_chunks(daily_dfs: Dict[datetime.date, pl.DataFrame], chunk_size: int = 15):
    chunks: Dict[datetime.date, List[pl.DataFrame]] = {}

    for date, day_df in daily_dfs.items():
        chunks[date] = []
        for slice in day_df.iter_slices(chunk_size):
            chunks[date].append(slice.select("hour", "title"))

    return chunks


def extract_interests_list(text: str) -> List[str]:
    match = re.search(r"\[(.*?)\]", text)
    if match:
        # If a match is found, split the substring by semicolon
        interests = match.group(1).replace('"', "").replace("'", "").split(";")
        return [interest.strip() for interest in interests]
    else:
        return []


def extract_interests_uniqueness_list(text: str) -> List[bool]:
    try:
        res = repair_json(text, return_objects=True)
        # Check if j is an array of booleans
        if isinstance(res, list) and all(isinstance(item, bool) for item in res):
            return res
    except Exception:
        pass
    return []


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

    chunked_interests, chunked_interests_uniqueness = zip(
        *[
            (
                extract_interests_list(res[-2]),
                extract_interests_uniqueness_list(res[-1]),
            )
            if res
            else ([], [])
            for res in results
        ]
    )

    # If the uniqueness are shorter than the interests, pad them with False so
    # that the final zip still goes through all the interests. If they are
    # longer, they will be truncated.
    chunked_interests_uniqueness = [
        uniqueness + [False] * (len(interests) - len(uniqueness))
        if len(uniqueness) < len(interests)
        else uniqueness[: len(interests)]
        for uniqueness, interests in zip(
            chunked_interests_uniqueness, chunked_interests
        )
    ]

    for date, interests, raw_interest, uniqueness in zip(
        dates, chunked_interests, raw_interests, chunked_interests_uniqueness
    ):
        yield {
            "date": date,
            "interests": interests,
            "interests_uniqueness": uniqueness,
            "count_invalid_interests": int(not interests),
            "count_invalid_uniqueness": int(not uniqueness),
            "raw_interests": raw_interest,
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
                pl.col("interests_uniqueness").flatten(),
                pl.col("raw_interests").flatten().unique(),
                pl.col("count_invalid_interests").sum(),
                pl.col("count_invalid_uniqueness").sum(),
            ]
        )
    )

    return FullHistorySessionsOutput(
        output_df=grouped_df,
        count_invalid_interests=int(grouped_df["count_invalid_interests"].sum()),
        count_invalid_uniqueness=int(grouped_df["count_invalid_uniqueness"].sum()),
    )
