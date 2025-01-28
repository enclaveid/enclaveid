from textwrap import dedent
from typing import Tuple

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from json_repair import repair_json

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.environments import get_environment
from data_pipeline.constants.whatsapp_conversations import (
    MIN_WHATSAPP_CONVERSATION_CHUNK_SIZE,
)
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.utils.get_messaging_partners import (
    get_messaging_partners,
)

DECISIONS = ["INCONCLUSIVE", "NO_CHUNK", "CHUNK"]


def _get_whatsapp_chunking_prompt_sequence(text: str) -> PromptSequence:
    return [
        dedent(
            f"""
          You will be given a list of messages from one of my private conversations for a single day.
          Examine the list of messages carefully and decide which of the following three actions to take:

          **INCONCLUSIVE**:
          Choose this if:
          - The messages do not provide enough clarity or information
          - The conversation is too short, too vague, or lacks substantive content.

          **CHUNK**:
          Choose this if the number of messages is greater than {MIN_WHATSAPP_CONVERSATION_CHUNK_SIZE} AND:
          - The conversation is long and contains many independent topics and segments (chunks). Messages in separate chunks must not be referring to each other.
          - Each chunk contains enough information to understand the participants’ intent and the broader context of the conversation.

          **NO_CHUNK**:
          Choose this if the number of messages is less than {MIN_WHATSAPP_CONVERSATION_CHUNK_SIZE} OR:
          - The conversation is not too long and contains enough information to be considered a single segment.
          - All messages relate to each other in a chain and cannot be separated

          Reason on your decision and conclude with a JSON with the exact structure shown below (and no additional keys or text):
          {{
            "decision": '{"' | '".join(DECISIONS)}',
            "chunks": [] | [
              {{
                "start_time": "HH:MM:SS",
                "end_time": "HH:MM:SS"
              }},
              ...
            ]
          }}

          Input Messages:
          {text}
          """
        ).strip()
    ]


def _parse_whatsapp_chunking_response(
    response: str
) -> Tuple[str, list[dict[str, str]]] | Tuple[None, None]:
    try:
        res = repair_json(response, return_objects=True)
        if isinstance(res, dict) and "decision" in res:
            if res["decision"] in DECISIONS:
                return res["decision"], res["chunks"]
            else:
                return (None, None)
        else:
            return (None, None)
    except Exception:
        return (None, None)


class WhatsappChunkingConfig(RowLimitConfig):
    row_limit: int | None = None if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "parsed_whatsapp_conversations": AssetIn(
            key=["parsed_whatsapp_conversations"],
        ),
    },
)
def whatsapp_conversation_chunks(
    context: AssetExecutionContext,
    config: Config,
    llama70b: BaseLlmResource,
    parsed_whatsapp_conversations: pl.DataFrame,
) -> pl.DataFrame:
    llm = llama70b
    messaging_partners = get_messaging_partners()

    df = (
        parsed_whatsapp_conversations.filter(
            pl.col("from").eq(messaging_partners.partner)
            | pl.col("to").eq(messaging_partners.partner)
        )
        .with_columns(
            message_str=pl.concat_str(
                [
                    pl.lit("From: "),
                    pl.col("from"),
                    pl.lit(", To: "),
                    pl.col("to"),
                    pl.lit(", Date: "),
                    pl.col("datetime").dt.strftime("%Y-%m-%d %H:%M:%S"),
                    pl.lit(", Content: "),
                    pl.col("content"),
                ]
            ),
            message_struct=pl.struct(
                [
                    pl.col("from"),
                    pl.col("to"),
                    pl.col("datetime").dt.time().cast(pl.Utf8).alias("time"),
                    pl.col("datetime")
                    .dt.date()
                    .cast(pl.Utf8)
                    .alias("date"),  # For downstream asset
                    pl.col("content"),
                ]
            ),
            date=pl.col("datetime").dt.date(),
        )
        .group_by("date")
        .agg(
            [
                pl.col("message_str").str.join("\n").alias("messages_str"),
                pl.col("message_struct").alias("messages_struct"),
            ]
        )
        .sort("date")
    )

    prompt_sequences = [
        _get_whatsapp_chunking_prompt_sequence(messages_str)
        for messages_str in df.get_column("messages_str").to_list()
    ]

    completions, cost = llm.get_prompt_sequences_completions_batch(prompt_sequences)

    decisions, chunks = zip(
        *[
            _parse_whatsapp_chunking_response(completion[-1])
            if completion
            else (None, None)
            for completion in completions
        ]
    )

    context.log.info(f"Total cost: ${cost:.2f}")

    return df.with_columns(
        decision=pl.Series(decisions, dtype=pl.Utf8),
        chunks=pl.Series(
            chunks,
            dtype=pl.List(
                pl.Struct(
                    [pl.Field("start_time", pl.Utf8), pl.Field("end_time", pl.Utf8)]
                )
            ),
        ),
    ).drop("messages_str")
