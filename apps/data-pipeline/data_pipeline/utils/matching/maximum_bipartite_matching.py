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
    embeddings1: np.ndarray,
    embeddings2: np.ndarray,
    labels1: np.ndarray,
    labels2: np.ndarray,
    invert: bool = False,
) -> pl.DataFrame:
    """
    Compute the maximum bipartite matching between two sets of embeddings
    with their corresponding cluster labels.
    Set invert to True if you want to match on dissimilarity instead of similarity.

    Returns a DataFrame with the following columns:
    - item_label_1: The cluster label of the first set of embeddings
    - item_label_2: The cluster label of the second set of embeddings
    - cosine_similarity: The cosine similarity between the two
    - cosine_distance: The cosine distance between the two
    """
    len1, len2 = len(embeddings1), len(embeddings2)
    max_len = max(len1, len2)

    # Pad both arrays to the same length
    padded_embeddings1 = _pad_array(embeddings1, max_len)
    padded_embeddings2 = _pad_array(embeddings2, max_len)
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

    # Convert to GPU arrays
    embeddings1_gpu = cp.asarray(padded_embeddings1)
    embeddings2_gpu = cp.asarray(padded_embeddings2)

    # Compute the pairwise cosine similarity matrix
    # Values between 0 and 2
    cost_matrix = pairwise_distances(embeddings1_gpu, embeddings2_gpu, metric="cosine")

    # Invert the cost matrix for dissimilarity
    if invert:
        cost_matrix = 2 - cost_matrix

    # Convert the cost matrix to a cuDF DataFrame for CuGraph
    df = cudf.DataFrame({"weight": cost_matrix.ravel(order="C")})
    cost, assignment = cugraph.dense_hungarian(df["weight"], max_len, max_len)

    # Calculate similarity from cosine distances
    indices1 = cp.arange(max_len)
    indices2 = cp.array(assignment.values)

    costs = cost_matrix[indices1, indices2].get()

    result_df = pl.DataFrame(
        {
            "item_label_1": padded_labels1[indices1.get().tolist()],
            "item_label_2": padded_labels2[indices2.get().tolist()],
            "cosine_similarity": (1 - costs).tolist(),
            "cosine_distance": costs.tolist(),
        }
    )

    # Remove padded values and return results in original order
    return result_df.filter(
        (pl.col("item_label_1") != PAD_VALUE) & (pl.col("item_label_2") != PAD_VALUE)
    )
