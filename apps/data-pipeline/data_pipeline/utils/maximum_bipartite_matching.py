from typing import TYPE_CHECKING

import polars as pl
from numpy import ndarray

from data_pipeline.utils.is_cuda_available import is_cuda_available

if is_cuda_available() or TYPE_CHECKING:
    import cudf
    import cugraph
    import cupy as cp
    from cuml.metrics import pairwise_distances


def maximum_bipartite_matching(
    user1_embeddings: ndarray, user2_embeddings: ndarray
) -> pl.DataFrame:
    len1 = len(user1_embeddings)
    len2 = len(user2_embeddings)

    # Determine which set of embeddings has more vectors
    if len1 >= len2:
        primary_embeddings = user1_embeddings
        secondary_embeddings = user2_embeddings
    else:
        # Swap if user1 has fewer embeddings than user2
        primary_embeddings = user2_embeddings
        secondary_embeddings = user1_embeddings
        len1, len2 = len2, len1  # Swap lengths accordingly

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

    # Mapping indices back if swapped
    if len1 < len2:
        # If we swapped the matrices, swap back the assignments
        user2_indices = cp.arange(len(assignment))
        user1_indices = cp.array(assignment.values)
    else:
        user1_indices = cp.arange(len(assignment))
        user2_indices = cp.array(assignment.values)

    # Calculate similarity from cosine distances
    similarities = 1 - cost_matrix[user1_indices, user2_indices].get()

    result_df = pl.DataFrame(
        {
            "user_cluster_label": user1_indices.get().tolist(),
            "other_user_cluster_label": user2_indices.get().tolist(),
            "cosine_similarity": similarities.tolist(),
        }
    )

    # Adjusted filtering logic to exclude dummy indices
    valid_user1_indices = set(range(len1))
    valid_user2_indices = set(range(len2))

    result_df = result_df.filter(
        (pl.col("user_cluster_label").is_in(valid_user1_indices))
        & (pl.col("other_user_cluster_label").is_in(valid_user2_indices))
    )

    return result_df
