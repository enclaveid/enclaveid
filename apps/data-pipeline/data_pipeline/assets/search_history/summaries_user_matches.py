import time
from textwrap import dedent

import polars as pl
from dagster import (
    AssetExecutionContext,
    asset,
)
from pydantic import Field

from data_pipeline.assets.search_history.summaries_embeddings import (
    summaries_embeddings,
)
from data_pipeline.consts import DAGSTER_STORAGE_BUCKET
from data_pipeline.utils.costs import get_gpu_runtime_cost
from data_pipeline.utils.matching.maximum_bipartite_matching import (
    maximum_bipartite_matching,
)

from ...constants.custom_config import RowLimitConfig
from ...constants.k8s import get_k8s_rapids_config
from ...partitions import user_partitions_def
from ...utils.capabilities import gpu_info


def create_prompt(user_id, activity_df, cluster_label, item_type):
    filtered_df = activity_df.filter(pl.col("cluster_label") == cluster_label)
    return dedent(
        f"""
        User {user_id}:
        {filtered_df[f"cluster_{item_type}"].item()}
        """
    )


def get_social_likelihood(activity_df, cluster_label):
    return activity_df.filter(pl.col("cluster_label") == cluster_label)[
        "social_likelihood"
    ].item()


def process_row(
    row,
    current_user_id,
    current_user_activity_df,
    other_user_id,
    other_user_activity_df,
):
    common_summary_prompt_items = dedent(
        create_prompt(
            current_user_id,
            current_user_activity_df,
            row["user_cluster_label"],
            "items",
        )
        + create_prompt(
            other_user_id,
            other_user_activity_df,
            row["other_user_cluster_label"],
            "items",
        )
    )

    common_summary_prompt_summaries = dedent(
        create_prompt(
            current_user_id,
            current_user_activity_df,
            row["user_cluster_label"],
            "summary",
        )
        + create_prompt(
            other_user_id,
            other_user_activity_df,
            row["other_user_cluster_label"],
            "summary",
        )
    )

    social_likelihoods = (
        get_social_likelihood(current_user_activity_df, row["user_cluster_label"]),
        get_social_likelihood(other_user_activity_df, row["other_user_cluster_label"]),
    )

    return (
        common_summary_prompt_items,
        common_summary_prompt_summaries,
        social_likelihoods,
    )


class SummariesUserMatchesConfig(RowLimitConfig):
    mean_of_comparison: str = Field(
        default="summary",
        description=(
            "The method to use for comparing the embeddings. "
            "Options are 'items' or 'summary'."
        ),
    )


@asset(
    partitions_def=user_partitions_def,
    deps=[summaries_embeddings],
    io_manager_key="parquet_io_manager",
    op_tags=get_k8s_rapids_config(1),
)
async def summaries_user_matches(
    context: AssetExecutionContext,
    config: SummariesUserMatchesConfig,
) -> pl.DataFrame:
    start_time = time.time()
    context.log.info(gpu_info())

    current_user_df = pl.read_parquet(
        DAGSTER_STORAGE_BUCKET
        / "summaries_embeddings"
        / f"{context.partition_key}.snappy"
    ).sort(by="cluster_label")

    result_df = pl.DataFrame(
        {
            "user_cluster_label": pl.Series([], dtype=pl.Int32),
            "other_user_cluster_label": pl.Series([], dtype=pl.Int32),
            "cosine_similarity": pl.Series([], dtype=pl.Float64),
            "other_user_id": pl.Series([], dtype=pl.Utf8),
            "activity_type": pl.Series([], dtype=pl.Utf8),
            "common_summary_prompt_items": pl.Series([], dtype=pl.Utf8),
            "common_summary_prompt_summaries": pl.Series([], dtype=pl.Utf8),
            "social_likelihoods": pl.Series([], dtype=pl.List(pl.Float64)),
        }
    )

    # Get a list of ready partitions in the parent asset
    other_user_ids = context.instance.get_materialized_partitions(
        context.asset_key_for_input("summaries_embeddings")
    )

    context.log.info(f"Matching with {len(other_user_ids)-1} users")

    # TODO Optimization: Do not recompute matches for the same pair of users
    for other_user_id in other_user_ids:
        if other_user_id == context.partition_key:
            continue

        other_user_df = pl.read_parquet(
            DAGSTER_STORAGE_BUCKET / "summaries_embeddings" / f"{other_user_id}.snappy"
        ).sort(by="cluster_label")

        for activity_type in ["knowledge_progression", "reactive_needs"]:
            current_user_activity_df = current_user_df.filter(
                pl.col("activity_type") == activity_type
            )
            other_user_activity_df = other_user_df.filter(
                pl.col("activity_type") == activity_type
            )

            if (
                not current_user_activity_df.is_empty()
                and not other_user_activity_df.is_empty()
            ):
                mean_of_comparison = f"{config.mean_of_comparison}_embedding"

                # Perform the bipartite matching for each user
                match_df = maximum_bipartite_matching(
                    current_user_activity_df[mean_of_comparison].to_numpy(),
                    other_user_activity_df[mean_of_comparison].to_numpy(),
                    current_user_activity_df["cluster_label"].to_numpy(),
                    other_user_activity_df["cluster_label"].to_numpy(),
                )

                # Add the other_user_id to the match_df
                match_df = match_df.with_columns(
                    [
                        pl.lit(other_user_id).alias("other_user_id"),
                        pl.lit(activity_type).alias("activity_type"),
                        pl.struct(match_df.columns).map_elements(
                            lambda row: process_row(
                                row,
                                context.partition_key,
                                current_user_activity_df,
                                other_user_id,
                                other_user_activity_df,
                            ),
                            return_dtype=pl.Struct(
                                [
                                    pl.Field("common_summary_prompt_items", pl.Utf8),
                                    pl.Field(
                                        "common_summary_prompt_summaries", pl.Utf8
                                    ),
                                    pl.Field("social_likelihoods", pl.List(pl.Float64)),
                                ]
                            ),
                        ),
                    ]
                )

                result_df = result_df.vstack(match_df)

    context.log.info(f"Estimated cost: ${get_gpu_runtime_cost(start_time):.2f}")

    return result_df.sort(by="cosine_similarity", descending=True)
