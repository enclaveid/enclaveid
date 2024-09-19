from typing import TYPE_CHECKING, Dict

import numpy as np

from data_pipeline.utils.capabilities import is_rapids_image

if is_rapids_image() or TYPE_CHECKING:
    import cuml
    import cupy as cp
else:
    cuml = None
    cp = None


def get_cluster_stats(cluster_labels: np.ndarray, prefix="") -> Dict[str, int]:
    cluster_stats = np.unique(cluster_labels, return_counts=True)
    return {
        f"{prefix}clusters_count": len(cluster_stats[0]),
        f"{prefix}noise_count": int(cluster_stats[1][0])
        if -1 in cluster_stats[0]
        else 0,
    }


def get_cluster_centroids(embeddings_gpu, cluster_labels: np.ndarray):
    cluster_centroids = []
    for cluster_label in np.unique(cluster_labels):
        if cluster_label == -1:
            continue
        cluster_embeddings = embeddings_gpu[cluster_labels == cluster_label]
        cluster_centroid = cp.mean(cluster_embeddings, axis=0)
        cluster_centroids.append(cluster_centroid)
    return cluster_centroids
