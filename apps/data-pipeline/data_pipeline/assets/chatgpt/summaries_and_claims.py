from textwrap import dedent
from typing import List

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json

from data_pipeline.assets.chatgpt.parsed_conversations import user_partitions_def
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.consts import get_environment
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.get_logger import get_logger


def get_conversation_summary_prompt_sequence(conversation_text: str) -> List[str]:
    return [
        dedent(
            f"""
            Summarize this conversation clearly identifying the main themes and the user intentions.
            Do not reintroduce too much information from the answers, unless the user is referencing it in their subsequent questions.
            Specifically state what the user will have obtained at the end of the conversation.

            {conversation_text}
            """
        ).strip(),
        dedent(
            """
            What can you infer about the user from this conversation?
            Separate the inference into medium-high confidence claims and low confidence speculations.
            Make the speculations as diverse and ambitious as possible, do not worry about them being low confidence as we will substantiate them later.
            """
        ).strip(),
        dedent(
            """
            Format the claims and speculations you've identified in JSON as follows:
            {
                "claims": [
                    "Claim 1",
                    "Claim 2",
                    ...
                ],
                "speculations": [
                    "Speculation 1",
                    "Speculation 2",
                    ...
                ]
            }

            Even if the "claims" are medium confidence, do not use conditional language.
            Limit the usage of conditional language to the "speculations".
            """
        ).strip(),
    ]


def parse_conversation_summary(text: str) -> tuple[List[str] | None, List[str] | None]:
    try:
        j = repair_json(text, return_objects=True)
        return (
            (j.get("claims", None), j.get("speculations", None))
            if isinstance(j, dict)
            else (None, None)
        )
    except Exception:
        return None, None


def parse_summaries_completions(completions: List[List[str]]):
    summaries, claims, speculations = zip(
        *[
            [x[0], *parse_conversation_summary(x[-1])] if x else (None, None, None)
            for x in completions
        ]
    )

    return {
        "summary": summaries,
        "claims": claims,
        "speculations": speculations,
    }


TEST_LIMIT = 10 if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "parsed_conversations": AssetIn(
            key=["parsed_conversations"],
        ),
    },
    op_tags=get_k8s_vllm_config(),
)
async def summaries_and_claims(
    context: AssetExecutionContext,
    parsed_conversations: pl.DataFrame,
    gemini_flash: BaseLlmResource,
) -> pl.DataFrame:
    logger = get_logger(context)

    df = (
        parsed_conversations.with_columns(
            pl.concat_str(
                [
                    pl.col("date"),
                    pl.lit(" at "),
                    pl.col("time"),
                    pl.lit("----------------------------------------"),
                    pl.lit("\n QUESTION: "),
                    pl.col("question"),
                    pl.lit("\n ANSWER: "),
                    pl.col("answer"),
                ],
            ).alias("conversation_text")
        )
        .group_by("conversation_id")
        .agg(
            [
                pl.col("conversation_text").str.concat("\n").alias("conversation_text"),
                pl.col("date").first().alias("start_date"),
                pl.col("time").first().alias("start_time"),
                pl.col("date").last().alias("end_date"),
                pl.col("time").last().alias("end_time"),
            ]
        )
    ).slice(0, TEST_LIMIT)

    logger.info(f"Processing {df.height} conversations...")

    prompt_sequences = [
        get_conversation_summary_prompt_sequence(row["conversation_text"])
        for row in df.to_dicts()
    ]

    (
        summaries_completions,
        cost,
    ) = gemini_flash.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {df.height} conversations.")
    logger.info(f"Execution cost: ${cost:.2f}")

    results = parse_summaries_completions(summaries_completions)

    result = df.hstack(pl.DataFrame(results))

    invalid_results = result.filter(
        pl.col("summary").is_null()
        | pl.col("claims").is_null()
        | pl.col("speculations").is_null()
    )

    if invalid_results.height > 0:
        logger.warning(f"Found {invalid_results.height} invalid summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    return result
