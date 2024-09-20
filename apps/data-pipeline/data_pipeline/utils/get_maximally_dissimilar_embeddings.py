from typing import TYPE_CHECKING

import numpy as np

from data_pipeline.utils.capabilities import is_rapids_image

if is_rapids_image() or TYPE_CHECKING:
    import cudf
    import cupy as cp
    from cuml.metrics import pairwise_distances
else:
    cudf = None
    cp = None
    pairwise_distances = None


# TODO: Cuml doesnt yet have multi gpu pairwise distance using dask backend
def get_maximally_dissimilar_embeddings(embeddings: np.ndarray) -> list[int]:
    embeddings_gpu = cp.asarray(embeddings)
    distances = pairwise_distances(embeddings_gpu, embeddings_gpu, metric="cosine")

    # Return the ranking of the embeddings by how dissimilar they are to all other points
    sum_distances = cp.sum(distances, axis=1)
    top_indices = cp.argsort(sum_distances)[::-1]

    return top_indices.tolist()


# Test the function
if __name__ == "__main__":
    embeddings = np.random.rand(100_000, 4096)
    print(get_maximally_dissimilar_embeddings(embeddings)[:5])
