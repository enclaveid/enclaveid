from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.consts import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)
from data_pipeline.utils.get_logger import get_logger


def get_conversation_skeleton_prompt_sequence(conversation: str) -> PromptSequence:
    return [
        # NB: do not use "user" or "assistant" in the prompt or it will throw a 500
        dedent(
            """
            Provide an essential summary of the conversation that preserves the user's unique perspective and thought process. Focus on capturing:

            1. User's Voice and Context
            - Preserve direct quotes or distinctive phrasings that reveal their thought process
            - Maintain their specific examples, analogies, or personal experiences
            - Keep emotional markers or signs of uncertainty/confidence

            2. Question Structure
            Primary elements (preserve in detail):
            - Personal reasoning and assumptions
            - Specific scenarios they describe
            - Their explicit or implicit goals
            - Any unique terminology or frame of reference they use

            Secondary elements (summarize briefly):
            - External information or context they reference
            - Technical details not specific to their situation
            - General background information

            3. Answer Format
            Represent the assistant's responses concisely, focusing only on key points that influenced the user's subsequent questions.

            Format each exchange as:
            Q at [datetime]: [Preserve detailed user voice and context] + [Brief summary of any external context]
            A at [datetime]: [Concise summary of main response points]

            Example:
            Q at 2024-01-01 12:00: "I've always stored my tomatoes in the fridge like my mom taught me" + Asks about optimal storage methods for extending shelf life
            A at 2024-01-01 12:01: Recommends room temperature storage instead of refrigeration

            Q at 2024-01-01 12:01: "That seems risky - my kitchen gets really warm and I've had fruit flies before" + Asks for specific timeline guidance
            A at 2024-01-01 12:02: Provides 5-7 day counter storage guideline with monitoring tips

            Here is the conversation:
            {conversation}
            """
        ).strip(),
    ]


TEST_LIMIT = 100 if get_environment() == "LOCAL" else None


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
async def conversation_skeletons(
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
                .str.concat("\n\n")
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
        get_conversation_skeleton_prompt_sequence(row["datetime_conversations"])
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
        {"skeleton": completion[-1] if completion else None}
        for completion in summaries_completions
    ]

    result = df.hstack(pl.DataFrame(results))

    invalid_results = result.filter(pl.col("skeleton").is_null())

    if invalid_results.height > 0:
        logger.warning(f"DOOT DOOT: Found invalid {invalid_results.height} skeletons.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    # TODO: why are there nulls?
    return result.filter(pl.col("datetime_conversations").is_not_null())
