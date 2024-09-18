import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple

import polars as pl
from dagster import get_dagster_logger
from json_repair import repair_json

from data_pipeline.resources.llm_inference.local_llm_resource import LocalLlmResource


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


# Skip the first list and extract the second one
def extract_interests_lists(text: str) -> Tuple[List[str], List[str]]:
    try:
        res = repair_json(text, return_objects=True)
        # Check if res is a list of two lists of strings
        if (
            isinstance(res, list)
            and len(res) == 2
            and all(isinstance(item, list) for item in res)
            and all(isinstance(item, str) for item in res[0])
            and all(isinstance(item, bool) for item in res[1])
        ):
            return res[0], res[1]
    except Exception:
        pass
    return ([], [])


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

    chunked_interests, chunked_interests_quirky = zip(
        *[extract_interests_lists(res[-1]) if res else ([], []) for res in results]
    )

    chunked_interests_quirkiness = [False] * len(chunked_interests)
    chunked_interests_quirkiness = chunked_interests_quirkiness + [True] * len(
        chunked_interests_quirky
    )

    chunked_interests = chunked_interests + chunked_interests_quirky

    for date, interests, raw_interest, quirkyness in zip(
        dates, chunked_interests, raw_interests, chunked_interests_quirkiness
    ):
        yield {
            "date": date,
            "interests": interests,
            "interests_quirkiness": quirkyness,
            "count_invalid_interests": int(not interests),
            "count_invalid_quirkiness": int(not quirkyness),
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
                pl.col("interests_quirkiness").flatten(),
                pl.col("raw_interests").flatten().unique(),
                pl.col("count_invalid_interests").sum(),
                pl.col("count_invalid_quirkiness").sum(),
            ]
        )
    )

    return FullHistorySessionsOutput(
        output_df=grouped_df.select(
            "date", "interests", "interests_quirkiness", "raw_interests"
        ),
        count_invalid_interests=int(grouped_df["count_invalid_interests"].sum()),
        count_invalid_quirkiness=int(grouped_df["count_invalid_quirkiness"].sum()),
    )
