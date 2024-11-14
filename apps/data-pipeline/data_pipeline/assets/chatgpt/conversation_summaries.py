from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from json_repair import repair_json

from data_pipeline.consts import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.utils.get_logger import get_logger


# TODO: is analysis necessary?
def get_conversation_summarization_prompt_sequence(conversation: str) -> PromptSequence:
    return [
        dedent(
            f"""
            Analyze this conversation focusing on how the questioner's thinking evolves. Specifically:

            1. What does their initial framing and word choice reveal about their understanding and goals?
            2. Track specific numbers, terms, or concepts they introduce, and what these suggest about their thinking
            3. How do they process and adapt to each new piece of information?
            4. What do their follow-up questions reveal about:
                - Their previous knowledge/preparation
                - Their underlying objectives
                - Their problem-solving approach
            5. How do their later questions connect back to their original intent?

            Conclude with what they gained beyond just information - include their evolving understanding and approach.

            If there the conversation has only one question, limit your answer to points 1 and 2.

            Here is the conversation:
            {conversation}
            """
        ).strip(),
        dedent(
            """
            Summarize your analysis as follows, alternating between user and assistant:
            Starting Mindset/Assumptions (user) -> New Information Encounter (assistant) -> Processing & Questions (user) -> New Information Encounter (assistant) -> ... -> Evolved Understanding (user)

            If the conversation has only one question, follow this format:
            Starting Mindset/Assumptions (user) -> New Information Encounter (assistant)

            Keep each item concise and to the point, but do not omit important details in the user's questions.
            """
        ).strip(),
        dedent(
            """
            Does the topic or the tone of this conversation have strongemotional implications?
            If so, list them as follows in chronological order:
            {{
                "strong_emotional_implications": list[str]
            }}
            Make sure to ground the emotional implications in the content of the conversation.

            If the conversation is rather practical and not emotional, return an empty list:
            {{
                "strong_emotional_implications": []
            }}
            """
        ).strip(),
    ]


def parse_strong_emotional_implications(text: str) -> list[str]:
    try:
        j = repair_json(text, return_objects=True)
        return j.get("strong_emotional_implications", []) if isinstance(j, dict) else []
    except Exception:
        return []


TEST_LIMIT = None if get_environment() == "LOCAL" else None


@asset(
    partitions_def=user_partitions_def,
    ins={
        "parsed_conversations": AssetIn(
            key=["parsed_conversations"],
        ),
    },
    io_manager_key="parquet_io_manager",
    # op_tags=get_k8s_vllm_config(),
)
async def conversation_summaries(
    context: AssetExecutionContext,
    gemini_flash: BaseLlmResource,
    parsed_conversations: pl.DataFrame,
):
    llm = gemini_flash
    logger = get_logger(context)

    df = (
        parsed_conversations.sort("date", "time")
        .with_columns(
            pl.concat_str(
                [
                    pl.col("date"),
                    pl.lit(" at "),
                    pl.col("time"),
                    pl.lit("\n QUESTION: "),
                    pl.col("question"),
                    pl.lit("\n ANSWER: "),
                    pl.col("answer"),
                ],
            ).alias("datetime_conversation"),
            pl.struct([pl.col("date"), pl.col("time"), pl.col("question")]).alias(
                "datetime_question"
            ),
        )
        .group_by("conversation_id")
        .agg(
            [
                pl.col("datetime_conversation")
                .str.concat("\nNEW CONVERSATION\n")
                .alias("datetime_conversations"),
                pl.col("title").first(),
                pl.col("date").first().alias("start_date"),
                pl.col("time").first().alias("start_time"),
                pl.col("datetime_question").alias("datetime_questions"),
            ]
        )
        .sort("start_date", "start_time")
    ).slice(0, TEST_LIMIT)

    prompt_sequences = [
        get_conversation_summarization_prompt_sequence(row["datetime_conversations"])
        for row in df.to_dicts()
    ]

    logger.info(f"Processing {len(prompt_sequences)} conversations...")

    (
        summaries_completions,
        cost,
    ) = llm.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing {len(prompt_sequences)} conversations.")
    logger.info(f"Execution cost: ${cost:.2f}")

    results = [
        {
            "analysis": completion[-3],
            "summary": completion[-2],
            "strong_emotional_implications": parse_strong_emotional_implications(
                completion[-1]
            ),
        }
        if completion
        else {"analysis": None, "summary": None, "strong_emotional_implications": []}
        for completion in summaries_completions
    ]

    result = df.hstack(pl.DataFrame(results)).with_columns(
        is_emotional=pl.col("strong_emotional_implications").list.len() > 0,
    )

    invalid_results = result.filter(
        pl.col("analysis").is_null() | pl.col("summary").is_null()
    )

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    # TODO: why are there nulls?
    return result.filter(pl.col("datetime_conversations").is_not_null())
