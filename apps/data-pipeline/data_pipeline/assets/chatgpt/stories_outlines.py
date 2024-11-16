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
            You are tasked to generate a compelling narrative given these emotional anchors for a given topic.
            To start off, which of these points would you pick to structure the narrative?
            Make sure they reveal a lot about about the protagonist and have causality between each other.

            Try to pick as many as you can:
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
    cluster_emotions = (
        conversations_clusters_summaries.filter(pl.col("is_emotional"))
        .with_columns(
            title_emotions=pl.concat_str(
                [
                    pl.col("start_date"),
                    pl.lit(" - "),
                    pl.col("title"),
                    pl.lit(":\n- "),
                    pl.col("strong_emotional_implications").list.join("\n- "),
                    pl.lit("\n\n"),
                ]
            )
        )
        .group_by("fine_cluster_label", "fine_cluster_summary", "coarse_cluster_label")
        .agg(
            title_emotions=pl.col("title_emotions").str.concat("\n"),
            average_fine_cluster_date=pl.col("start_date").str.to_date().mean(),
        )
        .with_columns(
            cluster_emotions=pl.concat_str(
                [
                    pl.lit("### "),
                    pl.col("fine_cluster_label"),
                    pl.lit(" - "),
                    pl.col("fine_cluster_summary"),
                    pl.lit(":\n\n"),
                    pl.col("title_emotions"),
                ]
            )
        )
        .sort("average_fine_cluster_date")
        .group_by("coarse_cluster_label")
        .agg(
            cluster_emotions=pl.col("cluster_emotions").str.concat("\n"),
            average_coarse_cluster_date=pl.col("average_fine_cluster_date")
            .dt.date()
            .mean(),
        )
        .sort("average_coarse_cluster_date")
    )

    # Generate prompts for each coarse cluster
    prompt_sequences = [
        get_story_outline_prompt(row["cluster_emotions"])
        for row in cluster_emotions.to_dicts()
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
    result = cluster_emotions.with_columns(story_outline=pl.Series(story_outlines))

    # Join back to original DataFrame to maintain all records
    # final_result = conversations_clusters_summaries.join(
    #     result.select(["coarse_cluster_label", "story_outline"]),
    #     on="coarse_cluster_label",
    #     how="left",
    # )

    return result
