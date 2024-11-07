from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    Config,
    asset,
)

from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.get_logger import get_logger


def get_conversation_summarization_prompt_sequence(conversation: str) -> list[str]:
    return [
        dedent(
            f"""
            Given this conversation, generate a quick summary of the conversation.

            Pay particular attention to:

            1. How did the user engage with the responder's answers?
            - Which concepts or approaches did they adopt in later messages?
            - How did they refine their questions based on received information?
            - Which parts influenced their subsequent messages?

            2. For the most recent response, briefly describe:
            - What were the key points made?
            - Which aspects seem most relevant to the user's needs?

            Here is the conversation:
            {conversation}
            """
        ).strip()
    ]


@asset(
    partitions_def=user_partitions_def,
    ins={
        "parsed_conversations": AssetIn(
            key=["parsed_conversations"],
        ),
    },
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(),
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
        {"summary": completion[-1]} if completion else None
        for completion in summaries_completions
    ]

    result = df.hstack(pl.DataFrame(results))

    invalid_results = result.filter(pl.col("summary").is_null())

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    return result
