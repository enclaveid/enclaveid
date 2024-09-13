from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from data_pipeline.utils.capabilities import is_rapids_image

if is_rapids_image() or TYPE_CHECKING:
    import cudf
    import cugraph
    import cupy as cp
    from cuml.metrics import pairwise_distances
else:
    cudf = None
    cugraph = None
    cp = None
    pairwise_distances = None

PAD_VALUE = -1


def _pad_array(arr, target_len):
    return np.pad(
        arr,
        ((0, target_len - len(arr)), (0, 0)),
        mode="constant",
        constant_values=PAD_VALUE,
    )


def maximum_bipartite_matching(
    user1_embeddings: np.ndarray,
    user2_embeddings: np.ndarray,
    user1_item_labels: np.ndarray,
    user2_item_labels: np.ndarray,
) -> pl.DataFrame:
    """
    Compute the maximum bipartite matching between two sets of embeddings
    with their corresponding cluster labels.
    """
    len1, len2 = len(user1_embeddings), len(user2_embeddings)
    max_len = max(len1, len2)

    # Pad both arrays to the same length
    padded_user1_embeddings = _pad_array(user1_embeddings, max_len)
    padded_user2_embeddings = _pad_array(user2_embeddings, max_len)
    padded_user1_labels = np.pad(
        user1_item_labels,
        (0, max_len - len1),
        mode="constant",
        constant_values=PAD_VALUE,
    )
    padded_user2_labels = np.pad(
        user2_item_labels,
        (0, max_len - len2),
        mode="constant",
        constant_values=PAD_VALUE,
    )

    # Convert to GPU arrays
    user1_embeddings_gpu = cp.asarray(padded_user1_embeddings)
    user2_embeddings_gpu = cp.asarray(padded_user2_embeddings)

    # Compute the pairwise cosine similarity matrix
    cost_matrix = pairwise_distances(
        user1_embeddings_gpu, user2_embeddings_gpu, metric="cosine"
    )

    # Convert the cost matrix to a cuDF DataFrame for CuGraph
    df = cudf.DataFrame({"weight": cost_matrix.ravel(order="C")})
    cost, assignment = cugraph.dense_hungarian(df["weight"], max_len, max_len)

    # Calculate similarity from cosine distances
    user1_indices = cp.arange(max_len)
    user2_indices = cp.array(assignment.values)
    similarities = 1 - cost_matrix[user1_indices, user2_indices].get()

    result_df = pl.DataFrame(
        {
            "user_item_label": padded_user1_labels[user1_indices.get().tolist()],
            "other_user_item_label": padded_user2_labels[user2_indices.get().tolist()],
            "cosine_similarity": similarities.tolist(),
        }
    )

    # Remove padded values and return results in original order
    return result_df.filter(
        (pl.col("user_item_label") != PAD_VALUE)
        & (pl.col("other_user_item_label") != PAD_VALUE)
    )
