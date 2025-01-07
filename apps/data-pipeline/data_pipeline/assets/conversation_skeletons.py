from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from json_repair import repair_json

from data_pipeline.constants.environments import get_environment
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


def get_conversation_skeleton_prompt_sequence(conversation: str) -> PromptSequence:
    return [
        # NB: do not use "user" or "assistant" in the prompt or it will throw a 500
        dedent(
            f"""
              Provide an essential summary of the conversation that preserves the user's unique perspective and thought process.
              The goal is to maintain maximum fidelity to the user's original voice while keeping the summary readable and focused.

              1. User's Voice and Context
              - Preserve direct quotes or distinctive phrasings that reveal their thought process
              - Maintain their specific examples, analogies, or personal experiences
              - Keep emotional markers or signs of uncertainty/confidence

              2. Question Structure and Length Handling
              For concise questions:
              - Preserve the entire question as written, maintaining all personal context and details

              For longer questions with distinct sections:
              - Preserve verbatim: The portions containing personal reasoning, experiences, or thought processes
              - Summarize only: Large blocks of external content (like pasted articles, code snippets, or reference materials)
              - Use the format: [Preserved personal content] + [Summary of external content]

              Example of handling a long question:
              Original question: "I've been struggling with my sourdough starter for weeks now - it just doesn't seem to rise like the ones I see online. I've tried feeding it twice a day but nothing helps. Here's the full recipe I've been following: [3 paragraphs of technical baking instructions pasted from a website]"

              Should become:
              Q: "I've been struggling with my sourdough starter for weeks now - it just doesn't seem to rise like the ones I see online. I've tried feeding it twice a day but nothing helps" + References a standard sourdough starter recipe with twice-daily feeding instructions

              3. Translate to English
              If the conversation is not in English, translate it to English.

              4. Answer Format
              Represent the assistant's responses concisely, focusing only on key points that influenced the user's subsequent questions.

              Format each exchange as:
              Q: [Complete question if concise] OR [Preserved personal content + Summarized external content]
              A: [Concise summary of main response points]

              Examples:
              Short question:
              Q: "I've always stored my tomatoes in the fridge like my mom taught me - is this the best way to keep them fresh?"
              A: Recommends room temperature storage instead of refrigeration

              Long question with external content:
              Q: "My garden tomatoes are getting spots and I'm really worried about losing the whole crop. My grandfather taught me to always check the leaves first" + [Includes lengthy paste of disease identification guide from gardening website]
              A: Identifies likely early blight and suggests organic treatment options

              5. Output schema
              Provide the output in the following JSON format:
              [
                  {{
                      "question": str,
                      "answer": str
                  }},
                  ...
              ]

              Here is the conversation:
              {conversation}
            """
        ).strip(),
    ]


def parse_conversation_skeletons(completion: str) -> list[dict] | None:
    try:
        res = repair_json(completion, return_objects=True)

        if isinstance(res, list) and all(
            isinstance(x, dict) and "question" in x and "answer" in x for x in res
        ):
            return res
        else:
            return None
    except Exception:
        return None


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
async def conversation_skeletons(
    context: AssetExecutionContext,
    llama70b: BaseLlmResource,
    parsed_conversations: pl.DataFrame,
):
    llm = llama70b
    logger = context.log

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
        # TODO: why are there nulls?
        .filter(
            pl.col("datetime_conversations").is_not_null()
            & (pl.col("datetime_conversations").str.len_chars() > 1)
        )
        .slice(0, TEST_LIMIT)
    )

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
        {
            "raw_skeleton": parse_conversation_skeletons(completion[-1])
            if completion
            else None
        }
        for completion in summaries_completions
    ]

    result = df.hstack(pl.DataFrame(results))

    invalid_results = result.filter(pl.col("raw_skeleton").is_null())

    if invalid_results.height > 0:
        logger.warning(f"DOOT DOOT: Found invalid {invalid_results.height} skeletons.")

    result = (
        result.join(invalid_results, on="conversation_id", how="anti")
        .with_columns(
            pl.struct(["datetime_questions", "raw_skeleton"])
            .map_elements(
                lambda row: [
                    {
                        "question": skel["question"],
                        "answer": skel["answer"],
                        "date": dtq["date"],
                        "time": dtq["time"],
                    }
                    for dtq, skel in zip(row["datetime_questions"], row["raw_skeleton"])
                ]
            )
            .alias("skeleton")
        )
        .drop("raw_skeleton")
    )

    return result
