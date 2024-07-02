import datetime
import re
from dataclasses import dataclass
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import polars as pl
from dagster import get_dagster_logger
from pydantic import BaseModel, Field

from .is_cuda_available import is_cuda_available

if is_cuda_available() or TYPE_CHECKING:
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
    from vllm import LLM, SamplingParams
else:
    torch = None
    SentenceTransformer = None
    LLM = SamplingParams = None
    AutoTokenizer = PreTrainedTokenizer = PreTrainedTokenizerFast = None


class InterestsSpec(BaseModel):
    name_prefix: str = Field(description="A prefix to add to the name of the asset.")
    first_instruction: str
    second_instruction: str


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


def vllm_generate(
    llm: LLM,
    tokenizer: Union[PreTrainedTokenizer, PreTrainedTokenizerFast],
    conversations: List[List[Dict[str, str]]],
):
    # TODO: How do we print the progress bar?
    return llm.generate(
        tokenizer.apply_chat_template(
            conversations,
            tokenize=False,
            add_generation_prompt=True,  # type: ignore
        ),
        # TODO: We could potentially make this part of the Config so the params can be
        # configured from the Dagster UI
        SamplingParams(temperature=0.8, top_p=0.95, max_tokens=1024),
    )


def generate_chunked_interests(
    ml_model_name: str,
    chunks: Dict[datetime.date, List[pl.DataFrame]],
    first_instruction: str,
    second_instruction: str,
):
    dates = []
    conversations: List[List[Dict[str, str]]] = []

    for date, day_dfs in chunks.items():
        for _, frame in enumerate(day_dfs, start=1):
            dates.append(date)
            conversations.append(
                [
                    {
                        "role": "user",
                        "content": f"{first_instruction}\n{frame}",
                    }
                ]
            )

    logger = get_dagster_logger()
    logger.info(f"Loading {ml_model_name}...")

    llm = LLM(ml_model_name)
    tokenizer = AutoTokenizer.from_pretrained(ml_model_name)

    first_requests = vllm_generate(llm, tokenizer, conversations)
    first_responses = [resp.outputs[0].text for resp in first_requests]

    for c, r1 in zip(conversations, first_responses):
        c.append({"role": "assistant", "content": r1})
        c.append({"role": "user", "content": second_instruction})

    second_requests = vllm_generate(llm, tokenizer, conversations)
    second_responses = [resp.outputs[0].text for resp in second_requests]

    for c, r2 in zip(conversations, second_responses):
        c.append({"role": "assistant", "content": r2})

    chunked_interests = [extract_interests_list(resp) for resp in second_responses]

    # Save the convo for each chunk as a single string
    chunked_convos = [
        "\n".join([f"{c['role']}: {c['content']}" for c in convo])
        for convo in conversations
    ]

    for date, interests, convos in zip(dates, chunked_interests, chunked_convos):
        interests = [interest for interest in (interests or []) if interest]

        yield {
            "date": date,
            "chunked_convos": convos,
            "interests": interests,
            "count_invalid_responses": 1 if len(interests) == 0 else 0,
        }


def get_full_history_sessions(
    full_takeout: pl.DataFrame,
    ml_model_name: str,
    chunk_size: int,
    first_instruction: str,
    second_instruction: str,
):
    logger = get_dagster_logger()

    # Split into multiple data frames (one per day). This is necessary to correctly
    # identify the data associated with each time entry.
    daily_dfs = full_takeout.with_columns(
        date=pl.col("timestamp").dt.date()
    ).partition_by("date", as_dict=True, include_key=False)

    logger.info(f"Processing {len(daily_dfs)} records")

    chunks = generate_chunks(daily_dfs, chunk_size)

    daily_records = generate_chunked_interests(
        ml_model_name, chunks, first_instruction, second_instruction
    )

    output_df = (
        pl.DataFrame(daily_records)
        .filter(pl.col("interests").is_not_null())
        .group_by("date")
        .agg(
            [
                pl.col("chunked_convos").str.concat("\n"),
                pl.col("interests").flatten().unique(),
                pl.col("count_invalid_responses").sum(),
            ]
        )
    )

    return FullHistorySessionsOutput(
        output_df=output_df,
        count_invalid_responses=int(output_df["count_invalid_responses"].sum()),
    )


def get_embeddings(series: pl.Series, model: SentenceTransformer):
    embeddings = model.encode(series.to_list(), precision="float32")
    return pl.Series(
        name="embeddings",
        values=embeddings,
        dtype=pl.Array(pl.Float32, model.get_sentence_embedding_dimension()),  # type: ignore
    )
