from typing import TYPE_CHECKING, List, Tuple

import numpy as np
import ray
from ray.experimental import tqdm_ray

from data_pipeline.utils.capabilities import is_vllm_image

NEG_INF: float = -np.inf

remote_tqdm = ray.remote(tqdm_ray.tqdm)

if is_vllm_image() or TYPE_CHECKING:
    import torch
else:
    torch = None


def greedy_embedding_matcher(
    embeddings1: torch.Tensor, embeddings2: torch.Tensor
) -> List[Tuple[int, int, float]]:
    """
    Match embeddings from two tensors using a greedy approach based on cosine similarity.

    This function calculates the cosine similarity between all pairs of embeddings
    from the two input tensors, then greedily matches them starting with the most
    similar pairs.

    Args:
    embeddings1 (torch.Tensor): First tensor of embeddings of shape (N1, D) on GPU
    embeddings2 (torch.Tensor): Second tensor of embeddings of shape (N2, D) on GPU

    Returns:
    List[Tuple[int, int, float]]: List of matches, each containing
        (index in embeddings1, index in embeddings2, similarity)
    """
    # Compute cosine similarities (matrix multiplication)
    similarities = torch.mm(embeddings1, embeddings2.t())

    # Flatten similarities and get sorted indices in descending order
    similarities_flat = similarities.view(-1)
    sorted_indices = torch.argsort(similarities_flat, descending=True)

    # Greedy matching
    matches = []
    used1 = set()
    used2 = set()
    N1, N2 = embeddings1.size(0), embeddings2.size(0)

    for idx in sorted_indices:
        i = idx // N2  # Row index in similarities (embedding1 index)
        j = idx % N2  # Column index in similarities (embedding2 index)
        i = i.item()
        j = j.item()
        if i not in used1 and j not in used2:
            sim = similarities[i, j].item()
            matches.append((i, j, sim))
            used1.add(i)
            used2.add(j)

            # Stop if all embeddings from either list are matched
            if len(used1) == N1 or len(used2) == N2:
                break

    return matches


@ray.remote(num_gpus=0.25, num_cpus=2)
class EmbeddingMatcher:
    def __init__(
        self,
        interest_aspects_embeddings: List[List[List[float]]],
        category_labels: List[int],
        aspect_similarity_threshold: float,
        bar: tqdm_ray.tqdm,
    ):
        self.device = torch.device("cuda")
        # Convert embeddings to torch tensors on GPU
        self.interest_aspects_embeddings = []
        for embeddings in interest_aspects_embeddings:
            if embeddings:
                embeddings_tensor = torch.tensor(embeddings, dtype=torch.float32).to(
                    self.device
                )
                self.interest_aspects_embeddings.append(embeddings_tensor)
            else:
                self.interest_aspects_embeddings.append(None)
        self.category_labels = category_labels  # Assume this is small
        self.aspect_similarity_threshold = aspect_similarity_threshold
        self.bar = bar

    def process_pairs(self, pairs: List[Tuple[int, int]]):
        results = []
        for i, j in pairs:
            result = self.process_pair(i, j)
            results.append(result)

        return results

    def process_pair(self, i: int, j: int):
        default_result = i, j, NEG_INF
        if self.category_labels[i] == self.category_labels[j]:
            return default_result

        aspect_embeddings_i = self.interest_aspects_embeddings[i]
        aspect_embeddings_j = self.interest_aspects_embeddings[j]

        if aspect_embeddings_i is None or aspect_embeddings_j is None:
            return default_result

        # Perform the matching on GPU
        matches = greedy_embedding_matcher(aspect_embeddings_i, aspect_embeddings_j)
        matches = [
            match for match in matches if match[2] >= self.aspect_similarity_threshold
        ]

        score = sum(match[2] for match in matches)

        self.bar.update.remote(1)

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

    # Generate list of pairs
    pairs = [
        (i, j) for i in range(interests_count) for j in range(i + 1, interests_count)
    ]

    # Determine the chunk size based on the total number of pairs and available resources
    # Assume each actor can process a chunk without exceeding GPU memory
    # You can adjust 'chunk_size' based on your data and GPU memory constraints
    chunk_size = 10000  # Adjust this value as needed
    pairs_chunks = [pairs[i : i + chunk_size] for i in range(0, len(pairs), chunk_size)]

    # Create actors dynamically and let Ray schedule them
    actors = []
    futures = []
    bar = remote_tqdm.remote(total=len(pairs))
    for chunk in pairs_chunks:
        actor = EmbeddingMatcher.remote(
            interest_aspects_embeddings,
            category_labels,
            aspect_similarity_threshold,
            bar,
        )
        actors.append(actor)
        future = actor.process_pairs.remote(chunk)
        futures.append(future)

    bar.close.remote()

    # Get results
    results = []
    for future in futures:
        results.extend(ray.get(future))

    # Fill scores_matrix
    for i, j, score in results:
        scores_matrix[i][j] = score

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
