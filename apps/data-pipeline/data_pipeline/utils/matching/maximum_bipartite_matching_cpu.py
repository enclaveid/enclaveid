import numpy as np
import polars as pl
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

PAD_VALUE = -1


def pad_array(arr, target_len):
    return np.pad(
        arr,
        ((0, target_len - len(arr)), (0, 0)),
        mode="constant",
        constant_values=PAD_VALUE,
    )


def maximum_bipartite_matching_cpu(
    embeddings1: np.ndarray,
    embeddings2: np.ndarray,
    labels1: np.ndarray,
    labels2: np.ndarray,
) -> pl.DataFrame:
    """
    Compute the maximum bipartite matching between two sets of embeddings
    with their corresponding cluster labels.
    Returns a DataFrame with the following columns:
    - item_label_1: The cluster label of the first set of embeddings
    - item_label_2: The cluster label of the second set of embeddings
    - cosine_similarity: The cosine similarity between the two
    - cosine_distance: The cosine distance between the two
    """
    len1, len2 = len(embeddings1), len(embeddings2)
    max_len = max(len1, len2)

    # Pad both arrays to the same length
    padded_embeddings1 = pad_array(embeddings1, max_len)
    padded_embeddings2 = pad_array(embeddings2, max_len)
    padded_labels1 = np.pad(
        labels1,
        (0, max_len - len1),
        mode="constant",
        constant_values=PAD_VALUE,
    )
    padded_labels2 = np.pad(
        labels2,
        (0, max_len - len2),
        mode="constant",
        constant_values=PAD_VALUE,
    )

    # Compute the pairwise cosine distance matrix
    cost_matrix = cdist(padded_embeddings1, padded_embeddings2, metric="cosine")

    # Negate the cost matrix to maximize pairwise similarity
    row_ind, col_ind = linear_sum_assignment(-cost_matrix)

    costs = cost_matrix[row_ind, col_ind]

    result_df = pl.DataFrame(
        {
            "item_label_1": padded_labels1[row_ind],
            "item_label_2": padded_labels2[col_ind],
            "cosine_similarity": 1 - costs,
            "cosine_distance": costs,
        }
    )

    # Remove padded values and return results in original order
    result_df = result_df.filter(
        (pl.col("item_label_1") != PAD_VALUE) & (pl.col("item_label_2") != PAD_VALUE)
    )

    return result_df
