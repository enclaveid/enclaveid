import time
from typing import List

import polars as pl
from dagster import AssetExecutionContext, asset

from data_pipeline.assets.search_history.interests_clusters import interests_clusters
from data_pipeline.assets.search_history.summaries_user_matches import (
    summaries_user_matches,
)
from data_pipeline.constants.custom_config import RowLimitConfig
from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.matching.maximum_bipartite_matching import (
    maximum_bipartite_matching,
)

from ...constants.k8s import get_k8s_rapids_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info


@asset(
    partitions_def=user_partitions_def,
    # TODO: maybe we should use ins with AllPartitionMapping ?
    deps=[summaries_user_matches, interests_clusters],
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_rapids_config(),
)
async def summaries_interests_matches(
    context: AssetExecutionContext,
    config: RowLimitConfig,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    current_user_id = context.partition_key
    summaries_user_matches_df = (
        pl.read_parquet(
            DAGSTER_STORAGE_BUCKET
            / "summaries_user_matches"
            / f"{current_user_id}.snappy"
        )
        .sort(by="cluster_label")
        .drop("common_summary_prompt_items", "common_summary_prompt_summaries")
    )

    current_user_df = pl.read_parquet(
        DAGSTER_STORAGE_BUCKET / "interests_clusters" / f"{current_user_id}.snappy"
    ).sort(by="interest_id")

    result_dfs: List[pl.DataFrame] = []

    for other_user_id in summaries_user_matches_df.get_column("other_user_id").unique():
        other_user_df = pl.read_parquet(
            DAGSTER_STORAGE_BUCKET / "interests_clusters" / f"{other_user_id}.snappy"
        ).sort(by="interest_id")

        # For each summaries_user_match, perform a bipartite matching with the
        # individual interests from interests_clusters
        for current_user_cluster_label, other_user_cluster_label in (
            summaries_user_matches_df.select(
                ["user_cluster_label", "other_user_cluster_label"]
            )
            .unique()
            .iter_rows()
        ):
            current_user_cluster_interests = current_user_df.filter(
                pl.col("cluster_label") == current_user_cluster_label
            )
            other_user_cluster_interests = other_user_df.filter(
                pl.col("cluster_label") == other_user_cluster_label
            )

            if (
                current_user_cluster_interests.is_empty()
                or other_user_cluster_interests.is_empty()
            ):
                continue

            match_df = (
                maximum_bipartite_matching(
                    current_user_cluster_interests["embeddings"].to_numpy(),
                    other_user_cluster_interests["embeddings"].to_numpy(),
                    current_user_cluster_interests["interest_id"].to_numpy(),
                    other_user_cluster_interests["interest_id"].to_numpy(),
                )
                .join(
                    current_user_cluster_interests.select(
                        pl.col("interest_id"),
                        pl.col("interests").alias("current_user_interest"),
                    ),
                    left_on="user_item_label",
                    right_on="interest_id",
                )
                .join(
                    other_user_cluster_interests.select(
                        pl.col("interest_id"),
                        pl.col("interests").alias("other_user_interest"),
                    ),
                    left_on="other_user_item_label",
                    right_on="interest_id",
                )
                .with_columns(
                    user_id=pl.lit(current_user_id),
                    other_user_id=pl.lit(other_user_id),
                )
                .rename(
                    {
                        "user_item_label": "user_interest_id",
                        "other_user_item_label": "other_user_interest_id",
                    }
                )
            )

            if not match_df.is_empty():
                result_dfs.append(match_df)

    result_df = pl.concat(result_dfs)

    context.log.info(f"Estimated cost: ${get_gpu_runtime_cost(start_time):.2f}")

    # No need to add back the cluster labels as the interest ids are unique
    # Columns: user_id, other_user_id, user_interest_id, other_user_interest_id, user_interest, other_user_interest, cosine_similarity
    return result_df.sort(by="cosine_similarity", descending=True)
