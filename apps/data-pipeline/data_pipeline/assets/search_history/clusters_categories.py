import time
from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from pydantic import Field

from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.constants.k8s import get_k8s_vllm_config
from data_pipeline.partitions import user_partitions_def
from data_pipeline.resources.inference.local_llms.gemma27b_resource import (
    Gemma27bResource,
)
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.parsing.json import parse_category_json


def get_categorization_prompt(cluster_interests: str) -> str:
    return dedent(
        f"""
    Analyze this list with a few samples from a given category of activities.

    After your analysis, come up with the most granluar possible category description that encompasses each record.
    Avoid providing a description that is too generic, enrich your answer with details on the contents.

    Conclude your answer in one line JSON format: {{ "description": "your answer" }}.
    Think step by step.

    {cluster_interests}
    """
    ).strip()


class ClustersCategoriesConfig(RowLimitConfig):
    max_samples: int = Field(
        default=100,
        description="The maximum number of samples for each cluster to use for categorization.",
    )


@asset(
    partitions_def=user_partitions_def,
    ins={
        "interests_clusters": AssetIn(
            key=["interests_clusters"],
        ),
    },
    io_manager_key="parquet_io_manager",
    # Need only 2 because there's isnt much data to process
    op_tags=get_k8s_vllm_config(2),
)
def clusters_categories(
    context: AssetExecutionContext,
    config: ClustersCategoriesConfig,
    gemma27b: Gemma27bResource,
    interests_clusters: pl.DataFrame,
) -> pl.DataFrame:
    start_time = time.time()
    logger = get_logger(context)

    # Sample max_samples from each merged cluster
    sampled_df = (
        interests_clusters.filter(pl.col("merged_cluster_label") != -1)
        .group_by("merged_cluster_label")
        .apply(lambda group: group.sample(n=min(len(group), config.max_samples)))
    )

    # Group interests by merged_cluster_label
    grouped_interests = (
        sampled_df.group_by("merged_cluster_label")
        .agg(pl.col("interests").alias("cluster_interests"))
        .sort("merged_cluster_label")
    )

    # Prepare prompts for each merged cluster
    prompt_sequences = [
        [get_categorization_prompt("\n".join(row["cluster_interests"]))]
        for row in grouped_interests.to_dicts()
    ]

    logger.info(f"Processing {len(prompt_sequences)} merged clusters...")

    # Get LLM completions
    completions, _ = gemma27b.get_prompt_sequences_completions_batch(prompt_sequences)

    logger.info(f"Done processing {len(prompt_sequences)} merged clusters.")

    # Parse completions
    categories = [parse_category_json(completion[-1]) for completion in completions]

    # Add categories to the grouped_interests DataFrame
    result = grouped_interests.with_columns(
        pl.Series(name="cluster_category", values=categories)
    )

    # Join the categories back to the original DataFrame
    final_result = interests_clusters.join(
        result.select(["merged_cluster_label", "cluster_category"]),
        on="merged_cluster_label",
        how="left",
    )

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time, 4):.2f}")

    return final_result
