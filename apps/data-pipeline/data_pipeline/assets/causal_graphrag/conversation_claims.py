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

            IMPORTANT: Each statement has to be self-contained, do not reference other statements:
            - NO: "The user is frustrated from this conversation"
            - YES: "The user is frustrated from not being able to debug the Django app"

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
Let's determine the causal relationships among inferrables (I) and observables (O).
Inferrables represent internal states or conclusions we draw, while observables are visible actions or events we can directly see.

Rules:
1. Temporal order matters - earlier events typically cause later ones
2. For closely related events, create direct observable-to-observable chains
3. New topics or state changes should flow through inferrable statements
4. Causation can only flow:
   - Downward (Inferrable → Observable)
   - Across (Observable → Observable, Inferrable → Inferrable)
   - Never upward (Observable → Inferrable)

For example, consider this learning-to-cook scenario:
[O] Watching cooking videos daily
[I] Developing interest in cooking
[O] Buying basic kitchen tools
[O] Following simple recipes
[I] Building cooking confidence
[O] Trying recipe modifications
[O] Sharing food pictures online
[O] Getting positive feedback

The causal chain would flow like this:
[O] Watching cooking videos daily → [I] Developing interest in cooking
[I] Developing interest in cooking → [O] Buying basic kitchen tools
[O] Buying basic kitchen tools → [O] Following simple recipes
[O] Following simple recipes → [I] Building cooking confidence
[I] Building cooking confidence → [O] Trying recipe modifications
[O] Trying recipe modifications → [O] Sharing food pictures online

Note that some events can have multiple causes. For example:
[O] Getting positive feedback is caused by both:
- [O] Sharing food pictures online → [O] Getting positive feedback
- [I] Building cooking confidence → [O] Getting positive feedback
(The confidence influences food quality, while sharing enables feedback)

Key principles to remember:
1. Observable-to-observable chains work for closely related events in the same state
2. Major state changes or topic shifts should flow through inferrable statements
3. Multiple events can cause a single outcome
4. Include as many statements as possible in your causal graph

When building your own causal chain, think about how events naturally progress and identify where state changes occur through inferrable conclusions.
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
        "conversation_skeletons": AssetIn(
            key=["conversation_skeletons"],
        ),
    },
    io_manager_key="parquet_io_manager",
    # op_tags=get_k8s_vllm_config(),
)
async def conversation_claims(
    context: AssetExecutionContext,
    gemini_pro: BaseLlmResource,
    conversation_skeletons: pl.DataFrame,
):
    llm = gemini_pro
    logger = get_logger(context)

    df = (
        conversation_skeletons
        # .sort("date", "time").with_columns(
        #     pl.concat_str(
        #         [
        #             pl.col("date"),
        #             pl.lit(" at "),
        #             pl.col("time"),
        #             pl.lit("\n QUESTION: "),
        #             pl.col("question"),
        #             pl.lit("\n ANSWER: "),
        #             pl.col("answer"),
        #         ],
        #     ).alias("datetime_conversation"),
        #     pl.struct([pl.col("date"), pl.col("time"), pl.col("question")]).alias(
        #         "datetime_question"
        #     ),
        # )
        # .group_by("conversation_id")
        # .agg(
        #     [
        #         pl.col("datetime_conversation")
        #         .str.concat("\n\n")
        #         .alias("datetime_conversations"),
        #         pl.col("title").first(),
        #         pl.col("date").first().alias("start_date"),
        #         pl.col("time").first().alias("start_time"),
        #         pl.col("datetime_question").alias("datetime_questions"),
        #     ]
        # )
        # .sort("start_date", "start_time")
    ).slice(0, TEST_LIMIT)

    prompt_sequences = [
        get_conversation_analysis_prompt_sequence(row["skeleton"])
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
            **parse_analysis_results(completion[0]),
            "causal_relationships": repair_json(completion[-1], return_objects=True),
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
    filtered_result = result.filter(pl.col("datetime_conversations").is_not_null())

    # Output:
    # ... | speculatives              | inferrables               | observables               | causal_relationships
    # ----|---------------------------|---------------------------|---------------------------|-----------------------
    # ... | List[{description,label}] | List[{description,label}] | List[{description,label}] | List[{source,target}]
    return filtered_result
