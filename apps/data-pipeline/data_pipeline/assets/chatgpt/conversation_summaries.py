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
            Briefly summarize this conversation.
            Pay attention to the details of the questions (rather than the answers) and try to infer the questioner's motivations and goals.

            Here is the conversation:
            {conversation}
            """
        ).strip(),
        # NB: do not use "user" or "assistant" in the prompt or it will throw a 500
        dedent(
            """
            Now provide an essential summary of the conversation.

            Keep each segment concise while preserving key details from the user's questions and the evolution of their understanding.
            Example:
            Q: Wonders if refrigeration is the best storage method for tomatoes to extend their shelf life -> A: Explains that cold temperatures harm tomatoes' quality and recommends room temperature storage -> Q: Questions the practicality of counter storage and seeks specific timeline information -> A: Provides concrete storage duration (5-7 days) and explains cold storage's negative effects on ripening
            """
        ).strip(),
        dedent(
            """
            Does the topic or the tone of the questions have strong emotional implications?
            IMPORTANT: It's likely that the conversation is rather practical so be conservative in your assessment.

            If so, list them as follows in chronological order:
            {{
                "strong_emotional_implications": list[str]
            }}
            Each item in the list should read like a claim about the user, for example:
            "The user places a lot of importance on finding a compatible partner."
            Do not use conditional language in the claims.

            Otherwise, return an empty list:
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
    gpt4o_mini: BaseLlmResource,
    parsed_conversations: pl.DataFrame,
):
    llm = gpt4o_mini
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
        else {
            "analysis": None,
            "summary": None,
            "strong_emotional_implications": [],
        }
        for completion in summaries_completions
    ]

    result = df.hstack(pl.DataFrame(results)).with_columns(
        is_emotional=pl.col("strong_emotional_implications").list.len() > 0,
    )

    invalid_results = result.filter(pl.col("summary").is_null())

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    # TODO: why are there nulls?
    return result.filter(pl.col("datetime_conversations").is_not_null())
