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
from data_pipeline.resources.inference.base_llm_resource import BaseLlmResource
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_logger import get_logger
from data_pipeline.utils.parsing.json import parse_category_json


def get_categorization_prompt_sequence(cluster_interests: str) -> list[str]:
    return [
        dedent(
            f"""
          Analyze this list and identify up to 5 main categories that best describe the contents of the list.
          For each main category, provide up to 3 sub categories that belong to it also found in the list.

          {cluster_interests}
        """
        ).strip(),
        dedent(
            """
          Format your answer in JSON: { "descriptive_categorization": "the categorical summary in string format" }.

          The descriptive_categorization string should follow this structure, for example:
          "Main category 1 (sub categories of 1 separated by comma), Main category 2 (sub categories of 2 separated by comma), ..."
        """
        ).strip(),
    ]


class ClustersCategoriesConfig(RowLimitConfig):
    max_samples: int = Field(
        default=50,
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
    # Could do with 2 because there's isnt much data to process
    op_tags=get_k8s_vllm_config(4),
)
def clusters_categories(
    context: AssetExecutionContext,
    config: ClustersCategoriesConfig,
    gemma27b: BaseLlmResource,
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
        get_categorization_prompt_sequence("\n".join(row["cluster_interests"]))
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

    logger.info(f"Execution cost: ${get_gpu_runtime_cost(start_time):.2f}")

    # Columns:
    # interest_id, date, cluster_interests,
    # interests_embeddings, cluster_label, merged_cluster_label
    # cluster_category
    return final_result
