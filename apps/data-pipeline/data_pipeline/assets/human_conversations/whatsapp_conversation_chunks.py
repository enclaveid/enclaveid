from textwrap import dedent
from typing import Tuple

import polars as pl
from dagster import AssetExecutionContext, AssetIn, Config, asset
from json_repair import repair_json

from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)

DECISIONS = ["INCONCLUSIVE", "NO_CHUNK", "CHUNK"]


def _get_whatsapp_chunking_prompt_sequence(text: str) -> PromptSequence:
    return [
        dedent(
            f"""
          You will be given a list of messages from one of my private conversations for a single day.
          Examine the list of messages carefully and decide which of the following three actions to take:

          **INCONCLUSIVE**:
          - Choose this if the messages do not provide enough clarity or information
            for you to meaningfully understand the participants’ intent or the broader
            context of the conversation. For example, if the conversation is too short,
            too vague, or lacks substantive content.

          **CHUNK**:
          - Choose this if the conversation is long and contains enough variation that it
            would be more useful to break it down into time-based segments (“chunks”).
            Each chunk should be independently analyzable and contain enough information
            to understand the participants’ intent and the broader context of the conversation.
            This means the chunks cannot be too short: if that's the case proceed with the
            "NO_CHUNK" decision.

          **NO_CHUNK**:
          - Choose this if the conversation is not too long and contains enough information to be considered a single segment.
            The chunk is independently analyzable and contain enough information
            to understand the participants’ intent and the broader context of the conversation.

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


# TODO
def _get_partner_name() -> str:
    if get_environment() == "LOCAL":
        return "Estela"

    raise NotImplementedError("Partner name not implemented for non-local environments")


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
    gpt4o: BaseLlmResource,
    parsed_whatsapp_conversations: pl.DataFrame,
) -> pl.DataFrame:
    partner_name = _get_partner_name()

    df = (
        parsed_whatsapp_conversations.filter(
            pl.col("from").eq(partner_name) | pl.col("to").eq(partner_name)
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

    completions, cost = gpt4o.get_prompt_sequences_completions_batch(prompt_sequences)

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
