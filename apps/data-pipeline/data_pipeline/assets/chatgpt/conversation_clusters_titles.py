from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)

from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.get_logger import get_logger


def get_fine_cluster_prompt_sequence(titles: str) -> list[str]:
    return [
        dedent(
            f"""
            Analyze these conversation titles and create a concise summary that captures
            the specific theme or topic of these conversations:

            {titles}
            """
        ).strip(),
        dedent(
            """
            Write a 1-2 sentence summary that captures the specific focus of these conversations.
            Respond with only the summary text, without any additional formatting or explanation.
            """
        ).strip(),
    ]


def get_coarse_cluster_prompt_sequence(summaries: str) -> list[str]:
    return [
        dedent(
            f"""
            Review these cluster summaries and create a concise, high-level title that captures
            the broader theme or category they represent:

            {summaries}
            """
        ).strip(),
        dedent(
            """
            Write a brief (2-5 words) but descriptive title that captures the general topic area.
            Respond with only the title text, without any additional formatting or explanation.
            """
        ).strip(),
    ]


@asset(
    partitions_def=user_partitions_def,
    ins={
        "conversations_clusters": AssetIn(
            key=["conversations_clusters"],
        ),
    },
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_vllm_config(4),
)
def conversation_clusters_titles(
    context: AssetExecutionContext,
    gemma27b: BaseLlmResource,
    conversations_clusters: pl.DataFrame,
) -> pl.DataFrame:
    llm = gemma27b
    logger = get_logger(context)

    # Filter out null titles
    filtered_clusters = conversations_clusters.filter(pl.col("title").is_not_null())

    fine_grouped = (
        filtered_clusters.group_by(["coarse_cluster_label", "fine_cluster_label"])
        .agg(pl.col("title").alias("conversation_titles"))
        .sort(["coarse_cluster_label", "fine_cluster_label"])
    )

    # Generate prompts for fine clusters
    fine_prompt_sequences = [
        get_fine_cluster_prompt_sequence("\n".join(row["conversation_titles"]))
        for row in fine_grouped.to_dicts()
    ]

    logger.info(f"Processing {len(fine_prompt_sequences)} fine clusters...")
    fine_completions, fine_cost = llm.get_prompt_sequences_completions_batch(
        fine_prompt_sequences
    )
    logger.info(f"Fine clusters cost: ${fine_cost:.2f}")

    # Parse fine cluster summaries (modified to use response directly)
    fine_summaries = [completion[-1].strip() for completion in fine_completions]
    fine_results = fine_grouped.with_columns(
        pl.Series(name="fine_cluster_summary", values=fine_summaries)
    )

    # Step 2: Generate coarse cluster titles
    coarse_grouped = (
        fine_results.group_by("coarse_cluster_label")
        .agg(pl.col("fine_cluster_summary").alias("fine_summaries"))
        .sort("coarse_cluster_label")
    )

    # Generate prompts for coarse clusters
    coarse_prompt_sequences = [
        get_coarse_cluster_prompt_sequence("\n".join(row["fine_summaries"]))
        for row in coarse_grouped.to_dicts()
    ]

    logger.info(f"Processing {len(coarse_prompt_sequences)} coarse clusters...")
    coarse_completions, coarse_cost = llm.get_prompt_sequences_completions_batch(
        coarse_prompt_sequences
    )
    logger.info(f"Coarse clusters cost: ${coarse_cost:.2f}")
    logger.info(f"Total cost: ${(fine_cost + coarse_cost):.2f}")

    # Parse coarse cluster titles (modified to use response directly)
    coarse_titles = [completion[-1].strip() for completion in coarse_completions]

    # Create final results
    result = coarse_grouped.with_columns(
        pl.Series(name="cluster_title", values=coarse_titles)
    )

    # Join both fine summaries and coarse titles back to the original DataFrame
    final_result = conversations_clusters.join(
        fine_results.select(["fine_cluster_label", "fine_cluster_summary"]),
        on="fine_cluster_label",
        how="left",
    ).join(
        result.select(["coarse_cluster_label", "cluster_title"]),
        on="coarse_cluster_label",
        how="left",
    )

    return final_result
