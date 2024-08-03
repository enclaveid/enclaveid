from typing import List, Sequence, Tuple

import polars as pl
from sqlalchemy import Row, func
from sqlalchemy.orm import Session

from data_pipeline.utils.database.db_models import (
    InterestsCluster,
    InterestsClusterMatch,
    InterestsClustersSimilarity,
    UserInterests,
)
from data_pipeline.utils.database.postgres import generate_cuid


def flatten(xss):
    return [x for xs in xss for x in xs]


def get_dict_leaf_values(d, leaves=None):
    if leaves is None:
        leaves = []

    if isinstance(d, dict):
        for value in d.values():
            get_dict_leaf_values(value, leaves)
    else:
        leaves.append(d)

    return leaves


def get_existing_matches(session: Session, cluster_ids: List[str]):
    return (
        session.query(InterestsClustersSimilarity)
        .join(InterestsClustersSimilarity.interestsClusterMatches)
        .filter(InterestsClusterMatch.interestsClusterId.in_(cluster_ids))
        .group_by(InterestsClustersSimilarity.id)
        .having(func.count(InterestsClusterMatch.id) == 2)
        .all()
    )


def insert_cluster_matches(
    current_user_interests_clusters: Sequence[Row[Tuple[InterestsCluster]]],
    other_user_interests_clusters: List[Row[Tuple[InterestsCluster, UserInterests]]],
    summaries_user_matches: pl.DataFrame,
    db_conn: Session,
):
    # Match the newly created clusters with the current user's clusters
    # by mapping the dataframe cluster ids to the database pipelineClusterIds
    current_user_cluster_ids_map = {
        cluster[0].pipelineClusterId: cluster[0].id
        for cluster in current_user_interests_clusters
    }

    # Edge case for the first user
    if len(other_user_interests_clusters) == 0:
        db_conn.commit()
        return

    other_users_clusters_ids_map = {}
    for cluster_record, user_interests_record in other_user_interests_clusters:
        user_id = user_interests_record.userId
        if user_id not in other_users_clusters_ids_map:
            other_users_clusters_ids_map[user_id] = {}
        other_users_clusters_ids_map[user_id][
            cluster_record.pipelineClusterId
        ] = cluster_record.id

    matches_to_insert = (
        summaries_user_matches.rename(
            {
                "cosine_similarity": "cosineSimilarity",
            }
        )
        .with_columns(
            [
                pl.col("user_cluster_label")
                .apply(lambda x: current_user_cluster_ids_map.get(x))
                .alias("currenClusterId"),
                pl.struct(["other_user_id", "other_user_cluster_label"])
                .apply(
                    lambda x: other_users_clusters_ids_map[x["other_user_id"]][  # type: ignore
                        x["other_user_cluster_label"]  # type: ignore
                    ]
                )
                .alias("otherClusterId"),
            ]
        )
        .select(
            [
                "cosineSimilarity",
                "currenClusterId",
                "otherClusterId",
            ]
        )
        .with_columns(
            id=pl.Series([generate_cuid() for _ in range(len(summaries_user_matches))]),
            updatedAt=pl.Series([func.now()] * len(summaries_user_matches)),
        )
        .to_dicts()
    )

    current_cluster_ids = set(get_dict_leaf_values(current_user_cluster_ids_map))
    other_cluster_ids = set(get_dict_leaf_values(other_users_clusters_ids_map))
    all_cluster_ids = current_cluster_ids.union(other_cluster_ids)

    # Get existing matches
    existing_matches = get_existing_matches(db_conn, list(all_cluster_ids))

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
            ((m["currenClusterId"], m["otherClusterId"]) for m in matches_to_insert),
        )
    )

    # Process matches in a single loop
    for match in matches_to_insert.copy():
        match_set = frozenset([match["currenClusterId"], match["otherClusterId"]])
        if match_set in existing_match_dict:
            matches_to_update.append(
                {
                    "id": existing_match_dict[match_set],
                    "cosineSimilarity": match["cosineSimilarity"],
                    "updatedAt": func.now(),
                }
            )
            matches_to_insert.remove(match)
            matches_to_insert_set.remove(match_set)

    # Update existing matches
    if matches_to_update:
        db_conn.bulk_update_mappings(InterestsClustersSimilarity, matches_to_update)

    if matches_to_insert:
        # Insert new matches
        db_conn.bulk_insert_mappings(
            InterestsClustersSimilarity,
            map(
                lambda x: {
                    "id": generate_cuid(),
                    "cosineSimilarity": x["cosineSimilarity"],
                    "updatedAt": func.now(),
                },
                matches_to_insert,
            ),
        )

        # Connect the new matches with the clusters
        db_conn.bulk_insert_mappings(
            InterestsClusterMatch,
            flatten(
                list(
                    map(
                        lambda x: [
                            {
                                "id": generate_cuid(),
                                "interestsClusterId": x["currenClusterId"],
                                "interestsClustersSimilarityId": existing_match_dict[
                                    frozenset(
                                        [x["currenClusterId"], x["otherClusterId"]]
                                    )
                                ],
                            },
                            {
                                "id": generate_cuid(),
                                "interestsClusterId": x["currenClusterId"],
                                "interestsClustersSimilarityId": existing_match_dict[
                                    frozenset(
                                        [x["currenClusterId"], x["otherClusterId"]]
                                    )
                                ],
                            },
                        ],
                        matches_to_insert,
                    )
                )
            ),
        )
