from typing import Any, List, Tuple

import numpy as np
import ray
from ray.experimental import tqdm_ray

from data_pipeline.utils.matching.greedy_embedding_matcher import (
    greedy_embedding_matcher,
)

NEG_INF: float = -np.inf

remote_tqdm = ray.remote(tqdm_ray.tqdm)


@ray.remote
def process_pair(
    i: int,
    j: int,
    interest_aspects_embeddings: List[List[Any]],
    category_labels: List[int],
    aspect_similarity_threshold: float,
    bar: tqdm_ray.tqdm,
):
    default_result = i, j, NEG_INF
    if category_labels[i] == category_labels[j]:
        return default_result

    aspect_embeddings_i = interest_aspects_embeddings[i]
    aspect_embeddings_j = interest_aspects_embeddings[j]

    if not aspect_embeddings_i or not aspect_embeddings_j:
        return default_result

    matches = greedy_embedding_matcher(aspect_embeddings_i, aspect_embeddings_j)
    matches = [match for match in matches if match[2] >= aspect_similarity_threshold]

    score = sum(match[2] for match in matches)

    bar.update.remote(1)

    if len(matches) > 0:
        return i, j, score
    else:
        return default_result


def aspects_matching(
    original_interest_ids: List[int],
    interest_aspects_embeddings: List[List[List[float]]],
    category_labels: List[int],
    aspect_similarity_threshold: float = 0.75,
) -> Tuple[List[int], List[float]]:
    ray.init()

    interests_count = len(interest_aspects_embeddings)
    scores_matrix = [[NEG_INF] * interests_count for _ in range(interests_count)]

    bar = remote_tqdm.remote(total=interests_count * (interests_count - 1) // 2)

    futures = []
    interest_aspects_embeddings_id = ray.put(interest_aspects_embeddings)
    for i in range(interests_count):
        for j in range(i + 1, interests_count):
            future = process_pair.remote(
                i,
                j,
                interest_aspects_embeddings_id,
                category_labels,
                aspect_similarity_threshold,
                bar,
            )
            futures.append(future)

    results = ray.get(futures)

    for i, j, score in results:
        scores_matrix[i][j] = score

    bar.close.remote()

    matching_interest_ids = [-1] * interests_count
    match_scores = [NEG_INF] * interests_count
    used_indices = set()

    for _ in range(interests_count):
        max_score = NEG_INF
        max_i, max_j = -1, -1
        for i in range(interests_count):
            if i in used_indices:
                continue
            for j in range(interests_count):
                if j in used_indices or i == j:
                    continue
                if scores_matrix[i][j] > max_score:
                    max_score = scores_matrix[i][j]
                    max_i, max_j = i, j

        if max_i != -1 and max_j != -1:
            matching_interest_ids[max_i] = original_interest_ids[max_j]
            match_scores[max_i] = max_score
            used_indices.add(max_i)
            used_indices.add(max_j)

    ray.shutdown()

    return matching_interest_ids, match_scores


if __name__ == "__main__":
    interest_aspects_embeddings = [
        [[0.1, 0.2], [0.3, 0.4]],  # Aspects for item 0
        [[0.5, 0.6], [0.7, 0.8]],  # Aspects for item 1
        [[0.9, 1.0], [1.1, 1.2]],  # Aspects for item 2
    ]
    category_labels = [0, 1, 0]  # Category labels for each item
    interest_ids = [100, 101, 102]  # IDs for each item

    matching_interest_ids, match_scores = aspects_matching(
        interest_ids, interest_aspects_embeddings, category_labels
    )
    print(matching_interest_ids)
    print(match_scores)
