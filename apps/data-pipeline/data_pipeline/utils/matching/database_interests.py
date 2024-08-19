from typing import List, Sequence, Tuple

import polars as pl
from sqlalchemy import Row, bindparam, func, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from data_pipeline.utils.data_structures import flatten, get_dict_leaf_values
from data_pipeline.utils.database.db_models import (
    InterestsCluster,
    InterestsClusterMatch,
    InterestsClustersSimilarity,
    UserInterests,
)
from data_pipeline.utils.database.postgres import generate_cuid


def _get_existing_matches(session: Session, cluster_ids: List[str]):
    return (
        session.query(InterestsClustersSimilarity)
        .join(InterestsClustersSimilarity.InterestsClusterMatch)
        .filter(InterestsClusterMatch.interestsClusterId.in_(cluster_ids))
        .group_by(InterestsClustersSimilarity.id)
        .having(func.count(InterestsClusterMatch.id) == 2)
        .all()
    )


# This function adds the matches between the current user's clusters and the other user's clusters
# to the database. It also updates the existing matches if they are already present in the database.
def insert_cluster_matches(
    current_user_interests_clusters: Sequence[Row[Tuple[InterestsCluster]]],
    other_user_interests_clusters: List[Row[Tuple[InterestsCluster, UserInterests]]],
    summaries_user_matches_with_desc: pl.DataFrame,
    db_conn: Session,
):
    # Match the newly created clusters with the current user's clusters
    # by mapping the dataframe cluster ids to the database pipelineClusterIds
    current_user_cluster_ids_map = {
        cluster[0].pipelineClusterId: cluster[0].id
        for cluster in current_user_interests_clusters
    }

    other_users_clusters_ids_map = {}
    for cluster_record, user_interests_record in other_user_interests_clusters:
        user_id = user_interests_record.userId
        if user_id not in other_users_clusters_ids_map:
            other_users_clusters_ids_map[user_id] = {}
        other_users_clusters_ids_map[user_id][
            cluster_record.pipelineClusterId
        ] = cluster_record.id

    matches_to_insert = (
        summaries_user_matches_with_desc.rename(
            {
                "cosine_similarity": "cosineSimilarity",
                "common_summary": "commonSummary",
                "common_title": "commonTitle",
            }
        )
        .with_columns(
            [
                pl.col("user_cluster_label")
                .apply(lambda x: current_user_cluster_ids_map.get(x))
                .alias("currentClusterId"),
                pl.struct(["other_user_id", "other_user_cluster_label"])
                .apply(
                    lambda x: other_users_clusters_ids_map[x["other_user_id"]][  # type: ignore
                        x["other_user_cluster_label"]  # type: ignore
                    ]
                )
                .alias("otherClusterId"),
                pl.col("social_likelihoods")
                .apply(lambda x: sum(x) / 2)
                .alias("averageSocialLikelihood"),
            ]
        )
        .select(
            [
                "averageSocialLikelihood",
                "cosineSimilarity",
                "currentClusterId",
                "otherClusterId",
                "commonSummary",
                "commonTitle",
            ]
        )
        .with_columns(
            id=pl.Series(
                [generate_cuid() for _ in range(len(summaries_user_matches_with_desc))]
            ),
            updatedAt=pl.Series([func.now()] * len(summaries_user_matches_with_desc)),
        )
        .to_dicts()
    )

    all_cluster_ids = set(get_dict_leaf_values(current_user_cluster_ids_map)).union(
        set(get_dict_leaf_values(other_users_clusters_ids_map))
    )

    # Get existing matches
    existing_matches = _get_existing_matches(db_conn, list(all_cluster_ids))

    # Create a dictionary for fast lookup of existing matches
    existing_match_dict = {
        frozenset(
            map(lambda x: x.interestsClusterId, match.InterestsClusterMatch)
        ): match.id
        for match in existing_matches
    }

    matches_to_update = []
    matches_to_insert_set = set(
        map(
            frozenset,
            ((m["currentClusterId"], m["otherClusterId"]) for m in matches_to_insert),
        )
    )

    # Process matches in a single loop
    for match in matches_to_insert.copy():
        match_set = frozenset([match["currentClusterId"], match["otherClusterId"]])
        if match_set in existing_match_dict:
            matches_to_update.append(
                {
                    "id": existing_match_dict[match_set],
                    "commonSummary": match["commonSummary"],
                    "commonTitle": match["commonTitle"],
                    "cosineSimilarity": match["cosineSimilarity"],
                    "averageSocialLikelihood": match["averageSocialLikelihood"],
                    "updatedAt": func.now(),
                }
            )
            matches_to_insert.remove(match)
            matches_to_insert_set.remove(match_set)

    # Update existing matches
    if matches_to_update:
        db_conn.execute(
            update(InterestsClustersSimilarity)
            .where(InterestsClustersSimilarity.id == bindparam("id"))
            .values(
                commonSummary=bindparam("commonSummary"),
                commonTitle=bindparam("commonTitle"),
                cosineSimilarity=bindparam("cosineSimilarity"),
                averageSocialLikelihood=bindparam("averageSocialLikelihood"),
                updatedAt=bindparam("updatedAt"),
            ),
            matches_to_update,
        )

    if matches_to_insert:
        # Insert new matches
        interest_clusters_similarity_ids = db_conn.execute(
            pg_insert(InterestsClustersSimilarity)
            .values(
                list(
                    map(
                        lambda x: {
                            "id": x["id"],
                            "cosineSimilarity": x["cosineSimilarity"],
                            "averageSocialLikelihood": x["averageSocialLikelihood"],
                            "updatedAt": x["updatedAt"],
                            "commonSummary": x["commonSummary"],
                            "commonTitle": x["commonTitle"],
                        },
                        matches_to_insert,
                    )
                )
            )
            .returning(InterestsClustersSimilarity.id)
        ).fetchall()

        # Connect the new matches with the clusters
        db_conn.execute(
            pg_insert(InterestsClusterMatch).values(
                flatten(
                    list(
                        map(
                            lambda m, i: [
                                {
                                    "id": generate_cuid(),
                                    "updatedAt": func.now(),
                                    "interestsClusterId": m["currentClusterId"],
                                    "interestsClustersSimilarityId": i[0],
                                },
                                {
                                    "id": generate_cuid(),
                                    "updatedAt": func.now(),
                                    "interestsClusterId": m["otherClusterId"],
                                    "interestsClustersSimilarityId": i[0],
                                },
                            ],
                            matches_to_insert,
                            interest_clusters_similarity_ids,
                        )
                    )
                ),
            )
        )
