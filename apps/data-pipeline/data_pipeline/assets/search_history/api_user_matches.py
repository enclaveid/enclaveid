import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    asset,
)
from sqlalchemy import func, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.resources.api_db_session import ApiDbSession
from data_pipeline.utils.database.db_models import (
    BigFive,
    InterestsCluster,
    MoralFoundations,
    UserInterests,
    UserTraits,
)
from data_pipeline.utils.database.postgres import generate_cuid
from data_pipeline.utils.matching.database_interests import insert_cluster_matches
from data_pipeline.utils.matching.database_users import insert_user_matches
from data_pipeline.utils.matching.overall_similarity_formula import (
    calculate_big5_similarity,
    calculate_interests_similarity,
    calculate_mft_similarity,
    calculate_overall_similarity,
)

from ...constants.custom_config import RowLimitConfig
from ...partitions import user_partitions_def


@asset(
    partitions_def=user_partitions_def,
    io_manager_key="parquet_io_manager",
    ins={
        "summaries_user_matches": AssetIn(key=["summaries_user_matches"]),
        "cluster_summaries": AssetIn(key=["cluster_summaries"]),
    },
)
def api_user_matches(
    context: AssetExecutionContext,
    config: RowLimitConfig,
    api_db: ApiDbSession,
    summaries_user_matches: pl.DataFrame,
    cluster_summaries: pl.DataFrame,
) -> None:
    db_conn = api_db.get_session()
    with db_conn.begin():
        user_interests_record_id = db_conn.execute(
            pg_insert(UserInterests)
            .values(
                id=generate_cuid(),
                userId=context.partition_key,
                updatedAt=func.now(),
            )
            .on_conflict_do_update(
                index_elements=[
                    UserInterests.userId,
                ],
                set_={
                    "id": UserInterests.id,
                },
            )
            .returning(UserInterests.id)
        ).fetchone()

        if user_interests_record_id is None:
            raise Exception(
                f"UserInterests record for {context.partition_key} could not be created"
            )

        # Insert clusters with summaries into the database
        current_user_interests_clusters = db_conn.execute(
            pg_insert(InterestsCluster)
            .values(
                cluster_summaries.rename(
                    {
                        "cluster_label": "pipelineClusterId",
                        "activity_type": "clusterType",
                        "cluster_summary": "summary",
                        "cluster_title": "title",
                        "is_sensitive": "isSensitive",
                        "cluster_dates": "activityDates",
                    }
                )
                .with_columns(
                    userInterestsId=pl.Series(
                        [user_interests_record_id[0]] * len(cluster_summaries)
                    ),
                    id=pl.Series(
                        [generate_cuid() for _ in range(len(cluster_summaries))]
                    ),
                    updatedAt=pl.Series([func.now()] * len(cluster_summaries)),
                )
                .to_dicts()
            )
            .on_conflict_do_update(
                index_elements=[
                    InterestsCluster.userInterestsId,
                    InterestsCluster.pipelineClusterId,
                    InterestsCluster.clusterType,
                ],
                set_={
                    "id": InterestsCluster.id,
                },
            )
            .returning(InterestsCluster)
        ).fetchall()

        # Get the InterestsCluster for the other users that we need to match with
        # including the UserInterests
        other_user_interests_clusters = (
            db_conn.query(InterestsCluster, UserInterests)
            .filter(
                or_(
                    *[
                        (UserInterests.userId == other_user_id)
                        & (
                            InterestsCluster.pipelineClusterId
                            == other_user_cluster_label
                        )
                        for other_user_id, other_user_cluster_label in summaries_user_matches[
                            ["other_user_id", "other_user_cluster_label"]
                        ]
                        .unique()
                        .to_numpy()
                    ]
                )
            )
            .filter(UserInterests.id == InterestsCluster.userInterestsId)
            .all()
        )

        insert_cluster_matches(
            current_user_interests_clusters,
            other_user_interests_clusters,
            summaries_user_matches,
            db_conn,
        )

        # Calculate the overall similarities
        current_user_traits = (
            db_conn.query(UserTraits, MoralFoundations, BigFive)
            .join(MoralFoundations, UserTraits.id == MoralFoundations.userTraitsId)
            .join(BigFive, UserTraits.id == BigFive.userTraitsId)
            .filter(UserTraits.userId == context.partition_key)
            .first()
        )

        if current_user_traits:
            other_users_traits = (
                db_conn.query(UserTraits, MoralFoundations, BigFive)
                .filter(
                    UserTraits.userId.in_(
                        [
                            user_interests_record.userId
                            for _, user_interests_record in other_user_interests_clusters
                        ]
                    )
                )
                .filter(UserTraits.id == MoralFoundations.userTraitsId)
                .filter(UserTraits.id == BigFive.userTraitsId)
                .all()
            )

            user_matches_to_insert = []
            _, current_user_mft, current_user_big5 = current_user_traits

            interests_similarities = summaries_user_matches.groupby(
                ["other_user_id", "activity_type"]
            ).agg([pl.col("cosine_similarity").apply(calculate_interests_similarity)])

            for other_user_t, other_user_mft, other_user_big5 in other_users_traits:
                mft_similarity = calculate_mft_similarity(
                    current_user_mft, other_user_mft
                )
                big5_similarity = calculate_big5_similarity(
                    current_user_big5, other_user_big5
                )
                proactive_interests_similarity = interests_similarities.filter(
                    (pl.col("other_user_id") == other_user_t.userId)
                    & (pl.col("activity_type") == "proactive")
                )["cosine_similarity"][0]

                reactive_interests_similarity = interests_similarities.filter(
                    (pl.col("other_user_id") == other_user_t.userId)
                    & (pl.col("activity_type") == "reactive")
                )["cosine_similarity"][0]

                overall_similarity = calculate_overall_similarity(
                    big5_similarity,
                    mft_similarity,
                    proactive_interests_similarity,
                    reactive_interests_similarity,
                )

                user_matches_to_insert.append(
                    {
                        "id": generate_cuid(),
                        "currentUserId": context.partition_key,
                        "otherUserId": other_user_t.userId,
                        "overallSimilarity": overall_similarity,
                        "updatedAt": func.now(),
                    }
                )

            if user_matches_to_insert:
                insert_user_matches(db_conn, user_matches_to_insert)

        db_conn.commit()
