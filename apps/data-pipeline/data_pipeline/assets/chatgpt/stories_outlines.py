from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.get_logger import get_logger


def get_story_outline_prompt(fine_cluster_summaries: list[str]) -> list[str]:
    summaries_text = "\n\n".join(
        f"fine cluster summary {i+1}:\n{summary}"
        for i, summary in enumerate(fine_cluster_summaries)
    )

    return [
        dedent(
            f"""
            Based on these emotional states, create a compelling story outline that encompasses the most compelling ones.

            {summaries_text}
            """
        ).strip()
    ]


@asset(
    partitions_def=user_partitions_def,
    ins={
        "conversations_clusters_summaries": AssetIn(
            key=["conversations_clusters_summaries"],
        ),
    },
    io_manager_key="parquet_io_manager",
)
def stories_outlines(
    context: AssetExecutionContext,
    gpt4o: BaseLlmResource,
    conversations_clusters_summaries: pl.DataFrame,
) -> pl.DataFrame:
    llm = gpt4o
    logger = get_logger(context)

    # Group by coarse cluster and filter for emotional clusters
    emotional_clusters = (
        conversations_clusters_summaries.filter(pl.col("is_emotional"))
        .with_columns(
            fine_cluster_emotions=pl.concat_str(
                [
                    pl.col("coarse_cluster_label"),
                    pl.lit(":"),
                    pl.col("fine_cluster_summary"),
                    pl.lit(":\n"),
                    pl.lit("- "),
                    pl.col("strong_emotional_implications").list.join("\n- "),
                ]
            )
        )
        .group_by("coarse_cluster_label")
        .agg(
            [
                pl.col("fine_cluster_emotions").alias("fine_clusters_emotions"),
            ]
        )
        .sort("coarse_cluster_label")
    )

    # Generate prompts for each coarse cluster
    prompt_sequences = [
        get_story_outline_prompt(row["fine_clusters_emotions"])
        for row in emotional_clusters.to_dicts()
    ]

    logger.info(
        f"Processing {len(prompt_sequences)} coarse clusters with emotional implications..."
    )
    completions, cost = llm.get_prompt_sequences_completions_batch(prompt_sequences)
    logger.info(f"Story outlines generation cost: ${cost:.2f}")

    # Parse story outlines
    story_outlines = [
        completion[-1].strip() if completion else None for completion in completions
    ]

    # Add story outlines to results
    result = emotional_clusters.with_columns(story_outline=pl.Series(story_outlines))

    # Join back to original DataFrame to maintain all records
    # final_result = conversations_clusters_summaries.join(
    #     result.select(["coarse_cluster_label", "story_outline"]),
    #     on="coarse_cluster_label",
    #     how="left",
    # )

    return result
