from typing import TYPE_CHECKING, List, Tuple

import numpy as np
import polars as pl

from data_pipeline.utils.capabilities import is_rapids_image
from data_pipeline.utils.matching.maximum_bipartite_matching import (
    maximum_bipartite_matching,
)

if is_rapids_image() or TYPE_CHECKING:
    import cudf
    import cugraph
    import cupy as cp
else:
    cp = None
    cudf = None
    cugraph = None


def aspect_bipartite_matching(
    original_interest_ids: List[int],
    interest_aspects_embeddings: List[np.ndarray],
    category_labels: List[int],
    aspect_similarity_threshold: float = 0.75,
) -> Tuple[List[int], List[float]]:
    """
    Perform aspect bipartite matching.

    Args:
        interest_aspects_embeddings (List[List[List[float]]]): List of interest aspects embeddings.
        category_labels (List[int]): List of category labels.
        aspect_similarity_threshold (float): Minimum similarity threshold for matching a single aspect.

    Returns:
        Tuple[List[int], List[float]]: Tuple of (matching_interest_id, match_score).
    """
    interests_count = len(interest_aspects_embeddings)

    cost_matrix = [[cp.inf] * interests_count for _ in range(interests_count)]

    for i in range(interests_count):
        for j in range(i + 1, interests_count):  # Avoid duplicates and self-matching
            if category_labels[i] == category_labels[j]:
                continue  # Skip matching items from the same category

            # Retrieve aspect embeddings for items i and j
            aspect_embeddings_i = interest_aspects_embeddings[i]
            aspect_embeddings_j = interest_aspects_embeddings[j]

            # Skip if any item has no aspects
            # if not aspect_embeddings_i or not aspect_embeddings_j:
            #     continue

            match_df = maximum_bipartite_matching(
                aspect_embeddings_i,
                aspect_embeddings_j,
                np.arange(len(aspect_embeddings_i)),
                np.arange(len(aspect_embeddings_j)),
            )

            match_df = match_df.filter(
                pl.col("cosine_similarity") > aspect_similarity_threshold
            )

            cost_matrix[i][j] = match_df["cosine_distance"].sum()

    cost_matrix = cp.array(cost_matrix)

    df = cudf.DataFrame({"weight": cost_matrix.ravel(order="C")})
    cost, assignment = cugraph.dense_hungarian(
        df["weight"], interests_count, interests_count
    )

    indices1 = cp.arange(interests_count)
    indices2 = cp.array(assignment.values)

    costs = cost_matrix[indices1, indices2].get()

    return original_interest_ids[indices2.get().tolist()], costs.tolist()


if __name__ == "__main__":
    interest_aspects_embeddings = [
        np.array([[0.1, 0.2], [0.3, 0.4]]),  # Aspects for item 0
        np.array([[0.5, 0.6], [0.7, 0.8]]),  # Aspects for item 1
        np.array([[0.9, 1.0], [1.1, 1.2]]),  # Aspects for item 2
    ]
    category_labels = [0, 1, 0]  # Category labels for each item
    interest_ids = [100, 101, 102]  # IDs for each item

    matching_interest_ids, match_scores = aspect_bipartite_matching(
        interest_ids, interest_aspects_embeddings, category_labels
    )
    print(matching_interest_ids)
    print(match_scores)
