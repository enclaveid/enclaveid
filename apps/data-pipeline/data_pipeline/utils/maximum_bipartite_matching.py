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
    # Find lengths and determine padding needed
    len1 = len(user1_embeddings)
    len2 = len(user2_embeddings)
    max_len = max(len1, len2)

    user1_embeddings_gpu = cp.asarray(user1_embeddings)
    user2_embeddings_gpu = cp.asarray(user2_embeddings)

    # Pad the smaller array with zeros
    if len1 < max_len:
        padding = cp.zeros((max_len - len1, user2_embeddings_gpu.shape[1]))
        user1_embeddings_gpu = cp.vstack((user1_embeddings_gpu, padding))
    elif len2 < max_len:
        padding = cp.zeros((max_len - len2, user1_embeddings_gpu.shape[1]))
        user2_embeddings_gpu = cp.vstack((user2_embeddings_gpu, padding))

    # Compute the pairwise cosine similarity matrix
    cost_matrix = pairwise_distances(
        user1_embeddings_gpu, user2_embeddings_gpu, metric="cosine"
    )

    # Convert the cost matrix to a cuDF DataFrame for CuGraph
    rows, cols = cost_matrix.shape
    df = cudf.DataFrame(
        {"weight": cost_matrix.ravel(order="C")}  # 'C' denotes row-major order
    )

    _, assignment = cugraph.dense_hungarian(df["weight"], rows, cols)

    # Convert assignment result to useful format
    # Each index corresponds to a user1 embedding and the value at that index to a user2 embedding
    user1_indices = cp.arange(len(assignment))
    user2_indices = cp.array(assignment.values)

    # Calculate similarity from cosine distances
    similarities = 1 - cost_matrix[user1_indices, user2_indices].get()

    # Remove padding
    return (
        pl.DataFrame(
            {
                "user_cluster_label": user1_indices.tolist(),
                "other_user_cluster_label": user2_indices.get().tolist(),
                "cosine_similarity": similarities.tolist(),
            }
        )
        .sort(by="cosine_similarity", descending=True)
        .head(min(len1, len2))
    )
