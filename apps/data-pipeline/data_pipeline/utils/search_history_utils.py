import datetime
import re
from dataclasses import dataclass
from typing import Dict, List

import polars as pl
from dagster import get_dagster_logger

from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource


@dataclass
class FullHistorySessionsOutput:
    output_df: pl.DataFrame
    count_invalid_responses: int


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


def generate_chunked_interests(
    llama8b: Llama8bResource,
    chunks: Dict[datetime.date, List[pl.DataFrame]],
    first_instruction: str,
    second_instruction: str,
):
    dates = []
    prompt_sequences = []
    raw_interests = []

    for date, day_dfs in chunks.items():
        for frame in day_dfs:
            dates.append(date)
            prompt_sequences.append(
                [f"{first_instruction}\n{frame}", second_instruction]
            )
            raw_interests.append(frame["title"].to_list())

    results, conversations = llama8b.get_prompt_sequences_completions_batch(
        prompt_sequences, [None, None]
    )

    chunked_interests = [
        extract_interests_list(res[-1]) if res else [] for res in results
    ]

    for date, chunked_interest, raw_interest in zip(
        dates, chunked_interests, raw_interests
    ):
        interests = [interest for interest in chunked_interest if interest]

        yield {
            "date": date,
            "interests": interests,
            "raw_interests": raw_interest,
            "count_invalid_responses": 1 if len(interests) == 0 else 0,
        }


def get_full_history_sessions(
    full_takeout: pl.DataFrame,
    chunk_size: int,
    first_instruction: str,
    second_instruction: str,
    llama8b: Llama8bResource,
):
    # Split into multiple data frames (one per day). This is necessary to correctly
    # identify the data associated with each time entry.
    daily_dfs = full_takeout.with_columns(
        date=pl.col("timestamp").dt.date()
    ).partition_by("date", as_dict=True, include_key=False)

    logger = get_dagster_logger()
    logger.info(f"Processing {len(daily_dfs)} records")

    chunks = generate_chunks(daily_dfs, chunk_size)

    daily_records = generate_chunked_interests(
        llama8b, chunks, first_instruction, second_instruction
    )

    output_df = (
        pl.DataFrame(daily_records)
        .filter(pl.col("interests").is_not_null())
        .group_by("date")
        .agg(
            [
                pl.col("interests").flatten().unique(),
                pl.col("raw_interests").flatten().unique(),
                pl.col("count_invalid_responses").sum(),
            ]
        )
    )

    return FullHistorySessionsOutput(
        output_df=output_df,
        count_invalid_responses=int(output_df["count_invalid_responses"].sum()),
    )
