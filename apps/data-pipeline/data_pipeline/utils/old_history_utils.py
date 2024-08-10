import datetime
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import polars as pl
from dagster import get_dagster_logger
from pydantic import BaseModel

from data_pipeline.resources.llm_inference.llama8b_resource import Llama8bResource


# TODO: types
class InterestsSpec(BaseModel):
    enrichment_prompt_sequence: List[Any]
    summarization_prompt_sequence: List[Any]


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


def extract_interests_list(text: str) -> Optional[List[str]]:
    match = re.search(r"\[(.*?)\]", text)
    if match:
        # If a match is found, split the substring by semicolon
        interests = match.group(1).replace('"', "").replace("'", "").split(";")
        return [interest.strip() for interest in interests]
    else:
        return None


def generate_chunked_interests(
    llama8b: Llama8bResource,
    chunks: Dict[datetime.date, List[pl.DataFrame]],
    first_instruction: str,
    second_instruction: str,
):
    dates = []
    prompt_sequences: List[List[str]] = []
    raw_interests = []

    for date, day_dfs in chunks.items():
        for frame in day_dfs:
            dates.append(date)
            prompt_sequences.append(
                [f"{first_instruction}\n{frame}", second_instruction]
            )
            raw_interests.append(frame["title"].to_list())

    results = llama8b.get_prompt_sequences_completions_batch(prompt_sequences)

    chunked_interests = [extract_interests_list(resp) for resp in results]

    for date, chunked_interest, raw_interest in zip(
        dates, chunked_interests, raw_interests
    ):
        interests = [interest for interest in (chunked_interest or []) if interest]

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


def parse_classification_result(raw_output: str):
    # Extract classification
    classification_match = re.search(r"Classification:\s*(.*)", raw_output)
    classification = classification_match.group(1) if classification_match else None

    # Extract confidence
    confidence_match = re.search(r"Confidence:\s*(\d+)%", raw_output)
    confidence = int(confidence_match.group(1)) / 100.0 if confidence_match else None

    # Extract sensitivity
    sensitivity_match = re.search(r"Sensitve:\s*(.*)", raw_output)
    is_sensitive = bool(sensitivity_match.group(1)) if sensitivity_match else None

    # Extract explanation
    explanation_match = re.search(r"Explanation:\s*(.*)", raw_output, re.DOTALL)
    explanation = explanation_match.group(1).strip() if explanation_match else None

    parsed_classification = (
        None
        if classification is None
        else {
            "classification": classification,
            "confidence": confidence,
            "explanation": explanation,
        }
    )

    main_category = None
    if parsed_classification is None or parsed_classification["confidence"] < 0.5:
        main_category = "unknown"
    else:
        if (
            "knowledge progression"
            in str(parsed_classification["classification"]).lower()
        ):
            main_category = "proactive"
        elif "reactive needs" in str(parsed_classification["classification"]).lower():
            main_category = "reactive"
        else:
            main_category = "unknown"

    return main_category, is_sensitive
