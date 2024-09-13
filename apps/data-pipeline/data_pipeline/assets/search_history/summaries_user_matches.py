import time
from textwrap import dedent
from typing import List

import polars as pl
from dagster import AssetExecutionContext, asset
from pydantic import Field

from data_pipeline.assets.search_history.interests_clusters import interests_clusters
from data_pipeline.assets.search_history.summaries_embeddings import (
    summaries_embeddings,
)
from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.get_materialized_partitions import get_materialized_partitions
from data_pipeline.utils.matching.maximum_bipartite_matching import (
    maximum_bipartite_matching,
)

from ...constants.custom_config import RowLimitConfig
from ...constants.k8s import get_k8s_rapids_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info

ACTIVITY_TYPES = ["knowledge_progression", "reactive_needs"]


class SummariesUserMatchesConfig(RowLimitConfig):
    mean_of_comparison: str = Field(
        default="summary",
        description="The method to use for comparing the summaries embeddings. Options are 'items' or 'summary'.",
    )


def generate_common_summary_prompt(
    user_id: str, other_user_id: str, user_data: str, other_user_data: str
) -> str:
    return dedent(
        f"""
        User {user_id}:
        {user_data}
        User {other_user_id}:
        {other_user_data}
        """
    )


def match_users(
    current_user_df: pl.DataFrame,
    other_user_df: pl.DataFrame,
    current_user_id: str,
    other_user_id: str,
    activity_type: str,
    mean_of_comparison: str,
) -> pl.DataFrame:
    current_user_activity_df = current_user_df.filter(
        pl.col("activity_type") == activity_type
    )
    other_user_activity_df = other_user_df.filter(
        pl.col("activity_type") == activity_type
    )

    if current_user_activity_df.is_empty() or other_user_activity_df.is_empty():
        return pl.DataFrame()

    comparison_column = f"{mean_of_comparison}_embedding"

    match_df = maximum_bipartite_matching(
        current_user_activity_df[comparison_column].to_numpy(),
        other_user_activity_df[comparison_column].to_numpy(),
        current_user_activity_df["cluster_label"].to_numpy(),
        other_user_activity_df["cluster_label"].to_numpy(),
    ).rename(
        {
            "user_item_label": "user_cluster_label",
            "other_user_item_label": "other_user_cluster_label",
        }
    )

    return match_df.with_columns(
        [
            pl.lit(other_user_id).alias("other_user_id"),
            pl.lit(activity_type).alias("activity_type"),
            pl.struct(match_df.columns)
            .map_elements(
                lambda row: generate_common_summary_prompt(
                    current_user_id,
                    other_user_id,
                    current_user_activity_df.filter(
                        pl.col("cluster_label") == row["user_cluster_label"]
                    )["cluster_items"].item(),
                    other_user_activity_df.filter(
                        pl.col("cluster_label") == row["other_user_cluster_label"]
                    )["cluster_items"].item(),
                )
            )
            .alias("common_summary_prompt_items"),
            pl.struct(match_df.columns)
            .map_elements(
                lambda row: generate_common_summary_prompt(
                    current_user_id,
                    other_user_id,
                    current_user_activity_df.filter(
                        pl.col("cluster_label") == row["user_cluster_label"]
                    )["cluster_summary"].item(),
                    other_user_activity_df.filter(
                        pl.col("cluster_label") == row["other_user_cluster_label"]
                    )["cluster_summary"].item(),
                )
            )
            .alias("common_summary_prompt_summaries"),
            pl.struct(match_df.columns)
            .map_elements(
                lambda row: (
                    current_user_activity_df.filter(
                        pl.col("cluster_label") == row["user_cluster_label"]
                    )["social_likelihood"].item(),
                    other_user_activity_df.filter(
                        pl.col("cluster_label") == row["other_user_cluster_label"]
                    )["social_likelihood"].item(),
                ),
            )
            .alias("social_likelihoods"),
        ]
    )


@asset(
    partitions_def=user_partitions_def,
    deps=[summaries_embeddings, interests_clusters],
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_rapids_config(1),
)
async def summaries_user_matches(
    context: AssetExecutionContext,
    config: SummariesUserMatchesConfig,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    current_user_id = context.partition_key
    current_user_df = pl.read_parquet(
        DAGSTER_STORAGE_BUCKET / "summaries_embeddings" / f"{current_user_id}.snappy"
    ).sort(by="cluster_label")

    other_user_ids = get_materialized_partitions(context, "summaries_embeddings")
    context.log.info(f"Matching with {len(other_user_ids)-1} users")

    result_dfs: List[pl.DataFrame] = []

    for other_user_id in other_user_ids:
        if other_user_id == current_user_id:
            continue

        other_user_df = pl.read_parquet(
            DAGSTER_STORAGE_BUCKET / "summaries_embeddings" / f"{other_user_id}.snappy"
        ).sort(by="cluster_label")

        for activity_type in ACTIVITY_TYPES:
            match_df = match_users(
                current_user_df,
                other_user_df,
                current_user_id,
                other_user_id,
                activity_type,
                config.mean_of_comparison,
            )
            if not match_df.is_empty():
                result_dfs.append(match_df)

    result_df = pl.concat(result_dfs)

    context.log.info(f"Estimated cost: ${get_gpu_runtime_cost(start_time):.2f}")

    # Columns: user_id, other_user_id, activity_type, common_summary_prompt_items, common_summary_prompt_summaries, social_likelihoods
    return result_df.sort(by="cosine_similarity", descending=True)
