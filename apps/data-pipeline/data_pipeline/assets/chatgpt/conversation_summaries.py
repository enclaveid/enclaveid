from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Config,
    asset,
)
from json_repair import repair_json

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.get_logger import get_logger


def get_conversation_summarization_prompt_sequence(conversation: str) -> list[str]:
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

            Keep your response concise and to the point, maximum 300 words.

            If there the conversation has only one question, limit your answer to points 1 and 2.

            Here is the conversation:
            {conversation}
            """
        ).strip(),
        dedent(
            """
            Does the topic or the tone of this conversation have strong emotional implications?

            After your analysis, provide your answer in JSON:
            {{
                "emotional": true | false
            }}
            """
        ).strip(),
    ]


def parse_emotional_analysis(text: str) -> bool | None:
    try:
        j = repair_json(text, return_objects=True)
        return j.get("emotional", None) if isinstance(j, dict) else None
    except Exception:
        return None


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
    config: Config,
    gemini_flash: BaseLlmResource,
    parsed_conversations: pl.DataFrame,
):
    llm = gemini_flash
    logger = get_logger(context)

    # Prepare conversations using the same format as conversations_embeddings
    df = (
        parsed_conversations.with_columns(
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
    )

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

    # Parse the completions
    results = [
        {
            "summary": completion[-2],
            "emotional": parse_emotional_analysis(completion[-1]),
        }
        if completion
        else {"summary": None, "emotional": None}
        for completion in summaries_completions
    ]

    result = df.hstack(pl.DataFrame(results))

    invalid_results = result.filter(pl.col("summary").is_null())

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    # TODO: why are there nulls?
    return result.filter(pl.col("datetime_conversations").is_not_null())
