from typing import List, Tuple

import numpy as np
from scipy.spatial.distance import cdist


def greedy_embedding_matcher(
    embeddings1: List[np.ndarray], embeddings2: List[np.ndarray]
) -> List[Tuple[int, int, float]]:
    """
    Match embeddings from two lists using a greedy approach based on cosine similarity.

    This function calculates the cosine similarity between all pairs of embeddings
    from the two input lists, then greedily matches them starting with the most
    similar pairs.

    Args:
    embeddings1 (List[np.ndarray]): First list of embeddings
    embeddings2 (List[np.ndarray]): Second list of embeddings

    Returns:
    List[Tuple[int, int, float]]: List of matches, each containing
        (index in embeddings1, index in embeddings2, similarity)
    """
    # Convert lists to numpy arrays
    emb1_array = np.array(embeddings1)
    emb2_array = np.array(embeddings2)

    # Calculate cosine distances (and convert to similarities)
    distances = cdist(emb1_array, emb2_array, metric="cosine")
    similarities = 1 - distances

    # Get sorted indices of similarities
    sorted_indices = np.argsort(similarities.ravel())[::-1]

    # Greedy matching
    matches = []
    used1 = set()
    used2 = set()

    for index in sorted_indices:
        i, j = np.unravel_index(index, similarities.shape)
        if i not in used1 and j not in used2:
            matches.append((i, j, similarities[i, j]))
            used1.add(i)
            used2.add(j)

        # Stop if all embeddings from either list are matched
        if len(used1) == len(embeddings1) or len(used2) == len(embeddings2):
            break

    return matches


# Example usage
if __name__ == "__main__":
    # Create some example embeddings
    emb1 = [np.array([1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])]
    emb2 = [
        np.array([0.1, 0.9, 0]),
        np.array([0.1, 0, 0.9]),
        np.array([0.33, 0.33, 0.33]),
        np.array([0.9, 0.1, 0]),
    ]

    matches = greedy_embedding_matcher(emb1, emb2)

    print("Matches (index1, index2, similarity):")
    for match in matches:
        print(f"({match[0]}, {match[1]}, {match[2]:.4f})")
