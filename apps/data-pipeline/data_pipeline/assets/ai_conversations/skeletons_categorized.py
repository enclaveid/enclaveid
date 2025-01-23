from textwrap import dedent

import polars as pl
from dagster import AssetExecutionContext, AssetIn, asset
from json_repair import repair_json

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.batch_inference.base_llm_resource import (
    BaseLlmResource,
    PromptSequence,
)


def get_cluster_summary_prompt_sequence(skeletons: list[str]) -> PromptSequence:
    formatted_skeletons = "\n\n".join([f"{i+1}. {s}" for i, s in enumerate(skeletons)])
    return [
        dedent(
            f"""
            Analyze this list and identify up to 5 main categories that best describe the contents of the list.
            For each main category, provide up to 3 sub categories that belong to it also found in the list.
            These can be much less if the list is short.

            Additionally, determine if this category is concerning "Personal/Humanistic Domain" or a "Professional/Practical Domain", for example:
            - Personal/Humanistic Domain: Health, relationships, personal growth, philosophy, art, etc.
            - Professional/Practical Domain: Work, technology, house chores, taxes, etc.

            Provide your response in this JSON structure, for example:
            {{
              "descriptive_categorization":"Main category 1 (sub categories of 1 separated by comma), Main category 2 (sub categories of 2 separated by comma), ...",
              "humanistic_domain": true | false
            }}


            Here is the list:
            {formatted_skeletons}
            """
        ).strip(),
    ]


def parse_category_summary(summary: str) -> tuple[str, bool]:
    try:
        res = repair_json(summary, return_objects=True)

        if isinstance(res, dict):
            return (
                res.get("descriptive_categorization", None),
                res.get("humanistic_domain", False),
            )
        elif isinstance(res, list):
            return (
                res[-1].get("descriptive_categorization", None),
                res[-1].get("humanistic_domain", False),
            )
        else:
            return "", False

    except Exception:
        return "", False


@asset(
    ins={
        "skeletons_clusters": AssetIn(
            key=["skeletons_clusters"],
        ),
    },
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
)
async def skeletons_categorized(
    context: AssetExecutionContext,
    gpt4o: BaseLlmResource,
    skeletons_clusters: pl.DataFrame,
) -> pl.DataFrame:
    """
    Generates category summaries for each cluster using LLM analysis of sample conversations.
    After computing the categories for each cluster, merges them back to the original dataframe.
    """
    logger = context.log
    df = skeletons_clusters

    # Group by cluster and sample up to 20 skeletons from each
    cluster_samples = (
        df.with_columns(
            pl.col("skeleton")
            .map_elements(
                lambda x: "\n".join(
                    [f"Q: {y['question']}\nA: {y['answer']}" for y in x]
                )
            )
            .alias("skeleton_text")
        )
        .group_by("cluster_label")
        .agg(
            [
                pl.col("skeleton_text").alias("skeleton_texts"),
            ]
        )
        .with_columns(
            [
                pl.col("skeleton_texts").list.slice(0, 20).alias("sample_skeletons"),
            ]
        )
    )

    # Generate prompts for each cluster
    prompt_sequences = [
        get_cluster_summary_prompt_sequence(row["sample_skeletons"])
        for row in cluster_samples.to_dicts()
    ]

    logger.info(f"Processing summaries for {len(prompt_sequences)} clusters...")

    # Get LLM completions
    summaries_completions, cost = gpt4o.get_prompt_sequences_completions_batch(
        prompt_sequences,
    )

    logger.info(f"Done processing cluster summaries. Cost: ${cost:.2f}")

    categories, is_personal = zip(
        *[
            parse_category_summary(completion[-1])
            for completion in summaries_completions
        ]
    )

    # Extract results
    category_summaries = pl.DataFrame(
        {
            "cluster_label": cluster_samples["cluster_label"],
            "category": categories,
            "is_personal": is_personal,
        }
    )

    # Merge the category results back to the original dataframe
    merged = df.join(
        category_summaries.select(["cluster_label", "category", "is_personal"]),
        on="cluster_label",
        how="left",
    )

    return merged
