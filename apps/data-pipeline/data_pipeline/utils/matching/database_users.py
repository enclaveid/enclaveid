from typing import List

from sqlalchemy import bindparam, func, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from data_pipeline.utils.data_structures import flatten
from data_pipeline.utils.database.db_models import UserMatch, UsersOverallSimilarity
from data_pipeline.utils.database.postgres import generate_cuid


def _get_existing_matches(db_conn: Session, user_ids: List[str]):
    return (
        db_conn.query(UsersOverallSimilarity)
        .join(UsersOverallSimilarity.UserMatch)
        .filter(UserMatch.userId.in_(user_ids))
        .group_by(UsersOverallSimilarity.id)
        .having(func.count(UserMatch.id) == 2)
        .all()
    )


def insert_user_matches(db_conn: Session, matches_to_insert: list[dict]):
    existing_matches = _get_existing_matches(
        db_conn,
        list(
            set(
                flatten(
                    list(
                        map(
                            lambda x: [x["currentUserId"], x["otherUserId"]],
                            matches_to_insert,
                        )
                    )
                )
            )
        ),
    )

    # Create a dictionary for fast lookup of existing matches
    existing_match_dict = {
        frozenset(map(lambda x: x.userId, match.UserMatch)): match.id
        for match in existing_matches
    }

    matches_to_update = []
    matches_to_insert_set = set(
        map(
            frozenset,
            ((m["currentUserId"], m["otherUserId"]) for m in matches_to_insert),
        )
    )

    # Process matches in a single loop
    for match in matches_to_insert.copy():
        match_set = frozenset([match["currentUserId"], match["otherUserId"]])
        if match_set in existing_match_dict:
            matches_to_update.append(
                {
                    "id": existing_match_dict[match_set],
                    "overallSimilarity": match["overallSimilarity"],
                    "updatedAt": func.now(),
                }
            )
            matches_to_insert.remove(match)
            matches_to_insert_set.remove(match_set)

    # Update existing matches
    if matches_to_update:
        db_conn.execute(
            update(UsersOverallSimilarity)
            .where(UsersOverallSimilarity.id == bindparam("id"))
            .values(
                overallSimilarity=bindparam("overallSimilarity"),
                updatedAt=bindparam("updatedAt"),
            ),
            matches_to_update,
        )

    if matches_to_insert:
        # Insert new matches
        users_overall_similarity_ids = db_conn.execute(
            pg_insert(UsersOverallSimilarity)
            .values(
                list(
                    map(
                        lambda x: {
                            "id": x["id"],
                            "overallSimilarity": x["overallSimilarity"],
                            "updatedAt": x["updatedAt"],
                        },
                        matches_to_insert,
                    )
                )
            )
            .returning(UsersOverallSimilarity.id)
        )

        # Connect the new matches with the clusters
        db_conn.execute(
            pg_insert(UserMatch).values(
                flatten(
                    list(
                        map(
                            lambda m, i: [
                                {
                                    "id": generate_cuid(),
                                    "updatedAt": func.now(),
                                    "userId": m["currentUserId"],
                                    "usersOverallSimilarityId": i[0],
                                },
                                {
                                    "id": generate_cuid(),
                                    "updatedAt": func.now(),
                                    "userId": m["otherUserId"],
                                    "usersOverallSimilarityId": i[0],
                                },
                            ],
                            matches_to_insert,
                            users_overall_similarity_ids,
                        )
                    )
                ),
            )
        )
