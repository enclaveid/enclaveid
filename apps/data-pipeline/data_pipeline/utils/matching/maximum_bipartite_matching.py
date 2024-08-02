from typing import TYPE_CHECKING

import polars as pl
from numpy import ndarray, pad

from data_pipeline.utils.capabilities import is_rapids_image

if is_rapids_image() or TYPE_CHECKING:
    import cudf
    import cugraph
    import cupy as cp
    from cuml.metrics import pairwise_distances

PAD_VALUE = -1


# TODO: Refactor, too complex
def maximum_bipartite_matching(
    user1_embeddings: ndarray,
    user2_embeddings: ndarray,
    user1_cluster_labels: ndarray,
    user2_cluster_labels: ndarray,
) -> pl.DataFrame:
    len1 = len(user1_embeddings)
    len2 = len(user2_embeddings)

    # Ensure the primary embeddings always have more elements
    # and pad the smaller array with zeros
    if len1 >= len2:
        primary_embeddings = user1_embeddings
        secondary_embeddings = user2_embeddings
        primary_labels = user1_cluster_labels
        secondary_labels = pad(
            user2_cluster_labels,
            (0, len1 - len2),
            mode="constant",
            constant_values=(PAD_VALUE),
        )
    else:
        primary_embeddings = user2_embeddings
        secondary_embeddings = user1_embeddings
        primary_labels = user2_cluster_labels
        secondary_labels = pad(
            user1_cluster_labels,
            (0, len2 - len1),
            mode="constant",
            constant_values=(PAD_VALUE),
        )

    primary_embeddings_gpu = cp.asarray(primary_embeddings)
    secondary_embeddings_gpu = cp.asarray(secondary_embeddings)

    # Compute the pairwise cosine similarity matrix
    cost_matrix = pairwise_distances(
        primary_embeddings_gpu, secondary_embeddings_gpu, metric="cosine"
    )

    # Convert the cost matrix to a cuDF DataFrame for CuGraph
    rows, cols = cost_matrix.shape
    df = cudf.DataFrame({"weight": cost_matrix.ravel(order="C")})

    cost, assignment = cugraph.dense_hungarian(df["weight"], rows, cols)

    # Remapping indices to cluster labels
    if len1 < len2:
        user2_indices = cp.arange(len(assignment))
        user1_indices = cp.array(assignment.values)
    else:
        user1_indices = cp.arange(len(assignment))
        user2_indices = cp.array(assignment.values)

    # Calculate similarity from cosine distances
    similarities = 1 - cost_matrix[user1_indices, user2_indices].get()

    result_df = pl.DataFrame(
        {
            "user_cluster_label": primary_labels[user1_indices.get().tolist()],
            "other_user_cluster_label": secondary_labels[user2_indices.get().tolist()],
            "cosine_similarity": similarities.tolist(),
        }
    )

    # Remove padded values
    return result_df.filter(
        (pl.col("user_cluster_label") != PAD_VALUE)
        & (pl.col("other_user_cluster_label") != PAD_VALUE)
    )
