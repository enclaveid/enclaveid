import asyncio
from typing import TYPE_CHECKING, List, Tuple

import numpy as np
import polars as pl
from tqdm import tqdm

from data_pipeline.utils.capabilities import is_rapids_image
from data_pipeline.utils.matching.maximum_bipartite_matching_cpu import (
    maximum_bipartite_matching_cpu,
)

if is_rapids_image() or TYPE_CHECKING:
    import cudf
    import cugraph
    import cupy as cp
else:
    cp = None
    cudf = None
    cugraph = None

FINITE_INF_VALUE: float = 999


async def process_pair(
    i, j, interest_aspects_embeddings, category_labels, aspect_similarity_threshold
):
    if category_labels[i] == category_labels[j]:
        return FINITE_INF_VALUE

    aspect_embeddings_i = interest_aspects_embeddings[i]
    aspect_embeddings_j = interest_aspects_embeddings[j]

    if not aspect_embeddings_i or not aspect_embeddings_j:
        return FINITE_INF_VALUE

    match_df = maximum_bipartite_matching_cpu(
        np.array(aspect_embeddings_i),
        np.array(aspect_embeddings_j),
        np.arange(len(aspect_embeddings_i)),
        np.arange(len(aspect_embeddings_j)),
    )

    match_df = match_df.filter(
        pl.col("cosine_similarity") > aspect_similarity_threshold
    )

    if match_df.height > 0:
        return match_df["cosine_distance"].sum()

    return FINITE_INF_VALUE


async def aspects_bipartite_matching(
    original_interest_ids: List[int],
    interest_aspects_embeddings: List[List[List[float]]],
    category_labels: List[int],
    aspect_similarity_threshold: float = 0.75,
) -> Tuple[List[int], List[float]]:
    interests_count = len(interest_aspects_embeddings)
    interest_ids = np.array(original_interest_ids)

    cost_matrix = [[FINITE_INF_VALUE] * interests_count for _ in range(interests_count)]

    tasks = []
    for i in range(interests_count):
        for j in range(i + 1, interests_count):
            task = asyncio.create_task(
                process_pair(
                    i,
                    j,
                    interest_aspects_embeddings,
                    category_labels,
                    aspect_similarity_threshold,
                )
            )
            tasks.append((i, j, task))

    for i, j, task in tqdm(tasks, total=len(tasks)):
        cost_matrix[i][j] = await task

    cost_matrix = cp.array(cost_matrix)

    df = cudf.DataFrame({"weight": cost_matrix.ravel(order="C")})
    cost, assignment = cugraph.dense_hungarian(
        df["weight"], interests_count, interests_count
    )

    indices1 = cp.arange(interests_count)
    indices2 = cp.array(assignment.values)

    matching_interest_ids = interest_ids[indices2.get().tolist()].tolist()
    match_scores = cost_matrix[indices1, indices2].get().tolist()

    for i, cost in enumerate(match_scores):
        if cost == FINITE_INF_VALUE:
            matching_interest_ids[i] = -1

    return matching_interest_ids, match_scores


if __name__ == "__main__":
    interest_aspects_embeddings = [
        [[0.1, 0.2], [0.3, 0.4]],  # Aspects for item 0
        [[0.5, 0.6], [0.7, 0.8]],  # Aspects for item 1
        [[0.9, 1.0], [1.1, 1.2]],  # Aspects for item 2
    ]
    category_labels = [0, 1, 0]  # Category labels for each item
    interest_ids = [100, 101, 102]  # IDs for each item

    matching_interest_ids, match_scores = asyncio.run(
        aspects_bipartite_matching(
            interest_ids, interest_aspects_embeddings, category_labels
        )
    )
    print(matching_interest_ids)
    print(match_scores)
