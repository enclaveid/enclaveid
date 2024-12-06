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


def get_conversation_analysis_prompt_sequence(conversation: str) -> PromptSequence:
    return [
        dedent(
            f"""
            You are tasked with analyzing Q&A conversations and categorizing statements into three levels of certainty: Observable, Inferrable, and Speculative.

            Observable: Direct evidence present in the data
            - Like reviewing security camera footage - simply stating what's there
            - Requires no interpretation, just accurate description
            - Any observer would agree on these facts
            Example: When someone asks "How do I configure PostgreSQL with Django?", we can observe they asked about Django-PostgreSQL integration - this is simply stating what's in the data

            Inferrable: Reasonable conclusions based on the evidence
            - Like a detective connecting pieces of evidence
            - Requires domain expertise to make logical connections
            - Most qualified observers would reach similar conclusions
            Example: If someone asks about Django basics, then deployment, then PostgreSQL integration, we can infer they're building a production web application - it's not directly stated but follows logically from the pattern

            Speculative: Possible underlying context given available information
            - Like a psychologist understanding motivations and life context from behaviors
            - Requires understanding of human/organizational behavior
            - Different analysts might reach different but valid conclusions
            Example: From the same Django/PostgreSQL questions, speculating "They're scaling their side project into a business" - while plausible, this involves more uncertainty

            CLASSIFICATION PROCESS:

            Read the Q&A conversation carefully and for each question, ask:
            - Can I quote text that directly proves this? → Observable
            - Can I connect multiple pieces of evidence to support this? → Inferrable
            - Am I making assumptions beyond the evidence? → Speculative

            IMPORTANT: For the speculatives, be as ambitious and broad as you can even if the results are low confidence. Highlight strong emotional implications if any.

            IMPORTANT: The claims have to be about the user, not the world, for example:
            - NO: "Class action lawsuits can hold corporations accountable for actions contributing to crony capitalism"
            - YES: "The user has learned that class action lawsuits can hold corporations accountable for actions contributing to crony capitalism"

            Output Format (JSON):
            [
              {{
                "statement": "Statement text",
                "category": "observable" | "inferrable" | "speculative",
                "label": "SHORT_STATEMENT_SUMMARY",
              }},
              ...
            ]

            For example:
            [
              {{
                "statement": "The user has been watching coding videos for months",
                "category": "observable",
                "label": "WATCHING_CODING_VIDEOS_FOR_MONTHS",
              }},
              ...
            ]

            Here is the conversation:
            {conversation}
            """
        ).strip(),
        dedent(
            """
            Let's now try to determine the causal relationships among inferrables and observables.

            Rules:
            - Temporal order matters - earlier events typically cause later ones
            - For closely related questions, create direct observable-to-observable chains
            - New topics or state changes should flow through inferrable statements
            - Causation can only flow:
               - Downward (Inferrable → Observable)
               - Across (Observable → Observable, Inferrable → Inferrable)
               - Never upward (Observable → Inferrable)

            For example, given the following statements:
            [O] Watching coding videos for months
            [O] Asking how to start Python
            [O] Asking about functions
            [O] Asking about Python classes
            [I] Moving from tutorials to practice
            [I] Beginning Python journey
            [O] Getting errors in class inheritance
            [O] Asking about unit testing classes
            [I] Building complex OOP project
            [O] Asking about design patterns
            [O] Requesting code review

            Key Decision Points:
            1. Basic Learning Chain:
               - The first few Python questions (basics → functions → classes) form a direct O→O chain
               - Why? They're closely related topics following natural progression without state change

            2. OOP State Change:
               - After several class-related questions, we infer a new state: "Building complex OOP project"
               - Why? The questions shifted from learning syntax to implementation challenges
               - This becomes a new causal background for subsequent questions

            3. Multiple Effects:
               - The "Building complex OOP project" state causes multiple parallel observations
               - Why? Complex projects typically generate several simultaneous learning needs

            4. Return to Direct Chain:
               - Design patterns → code review is direct O→O
               - Why? These are closely related activities within the same state

            Example causal chain:
            [I] Beginning Python journey -> [I] Moving from tutorials to practice
            [I] Moving from tutorials to practice -> [O] Asking how to start Python
            [O] Asking how to start Python -> [O] Asking about functions
            [O] Asking about functions -> [O] Asking about Python classes
            [O] Asking about Python classes -> [I] Building complex OOP project
            [I] Building complex OOP project -> [O] Getting errors in class inheritance
            [I] Building complex OOP project -> [O] Asking about unit testing classes
            [I] Building complex OOP project -> [O] Asking about design patterns
            [O] Asking about design patterns -> [O] Requesting code review
            """
        ).strip(),
        # Graph structure:
        #
        #                    Beginning Python journey
        #                            |
        #                            v
        #                Moving from tutorials
        #                    |
        #                    v
        # Watching videos -> Asking Python basics -> Functions -> Classes
        #                                                           |
        #                                                           v
        #                                                  Building OOP project
        #                                                    /      |      \
        #                                                   /       |       \
        #                                                  v        v        v
        #                                           Inheritance  Testing  Design patterns
        #                                                                      |
        #                                                                      v
        #                                                                 Code review
        dedent(
            """
            Format your output in JSON as a graph edge list, using the labels from the first step:
            [
              {{"source": "LABEL1", "target": "LABEL2"}},
              ...
            ]
            """
        ).strip(),
    ]


def parse_analysis_results(text: str) -> dict:
    try:
        j = repair_json(text, return_objects=True)
        if not isinstance(j, list):
            return {"speculatives": [], "inferrables": [], "observables": []}

        result = {"speculatives": [], "inferrables": [], "observables": []}

        for item in j:
            category = item.get("category", "").lower()
            if category in ["speculative", "inferrable", "observable"]:
                result[f"{category}s"].append(
                    {
                        "description": item["statement"],
                        "label": item["label"],
                    }
                )

        return result
    except Exception:
        return {"speculatives": [], "inferrables": [], "observables": []}


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
async def conversation_claims(
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
        get_conversation_analysis_prompt_sequence(row["datetime_conversations"])
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
            **parse_analysis_results(completion[-3]),
            "causal_relationships": repair_json(completion[-1]),
        }
        if completion
        else {
            "speculatives": None,
            "inferrables": None,
            "observables": None,
            "causal_relationships": None,
        }
        for completion in summaries_completions
    ]

    result = df.hstack(pl.DataFrame(results))

    invalid_results = result.filter(pl.col("causal_relationships").is_null())

    if invalid_results.height > 0:
        logger.warning(f"Found invalid {invalid_results.height} summaries.")

    result = result.join(invalid_results, on="conversation_id", how="anti")

    # TODO: why are there nulls?
    return result.filter(pl.col("datetime_conversations").is_not_null())
