import polars as pl
from dagster import AssetExecutionContext, AssetIn, Optional, asset

from ...constants.custom_config import RowLimitConfig
from ...partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "summaries_user_matches_with_desc": AssetIn(
            key=["summaries_user_matches_with_desc"],
            dagster_type=Optional[pl.DataFrame],
        ),
        "cluster_summaries": AssetIn(key=["cluster_summaries"]),
    },
    op_tags={"hook": "notify_api_on_success"},
)
def results_for_api(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    summaries_user_matches_with_desc: pl.DataFrame | None,
    cluster_summaries: pl.DataFrame,
) -> pl.DataFrame:
    # Process cluster summaries
    processed_cluster_summaries = process_cluster_summaries(cluster_summaries)

    # Process user matches if available
    if summaries_user_matches_with_desc is not None:
        processed_user_matches = process_user_matches(summaries_user_matches_with_desc)

        # Join processed_cluster_summaries with processed_user_matches
        joined_data = processed_cluster_summaries.join(
            processed_user_matches,
            left_on="pipelineClusterId",
            right_on="user_cluster_label",
            how="left",
        )
    else:
        joined_data = processed_cluster_summaries

    # Add user ID and timestamp
    final_data = joined_data.with_columns(
        [
            pl.lit(context.partition_key).alias("userId"),
        ]
    )

    return final_data


def process_cluster_summaries(cluster_summaries: pl.DataFrame) -> pl.DataFrame:
    return cluster_summaries.rename(
        {
            "cluster_label": "pipelineClusterId",
            "activity_type": "clusterType",
            "cluster_summary": "summary",
            "cluster_title": "title",
            "is_sensitive": "isSensitive",
            "cluster_dates": "activityDates",
            "cluster_items": "clusterItems",
            "social_likelihood": "socialLikelihood",
        }
    ).with_columns(
        [
            pl.col("clusterItems").str.split("\n"),
        ]
    )


def process_user_matches(
    summaries_user_matches_with_desc: pl.DataFrame,
) -> pl.DataFrame:
    return (
        summaries_user_matches_with_desc.rename(
            {
                "cosine_similarity": "cosineSimilarity",
                "common_summary": "commonSummary",
                "common_title": "commonTitle",
            }
        )
        .with_columns(
            [
                pl.col("social_likelihoods")
                .apply(lambda x: sum(x) / 2)
                .alias("averageSocialLikelihood"),
            ]
        )
        .select(
            [
                "cosineSimilarity",
                "commonSummary",
                "commonTitle",
                "averageSocialLikelihood",
                "user_cluster_label",
                "other_user_id",
                "other_user_cluster_label",
            ]
        )
    )
