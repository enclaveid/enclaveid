from typing import Dict

from data_pipeline.utils.capabilities import is_rapids_image

if is_rapids_image():
    import cupy as xp
else:
    import numpy as xp


def get_cluster_stats(cluster_labels: xp.ndarray, prefix="") -> Dict[str, int]:
    cluster_stats = xp.unique(cluster_labels, return_counts=True)
    return {
        f"{prefix}clusters_count": len(cluster_stats[0]),
        f"{prefix}noise_count": int(cluster_stats[1][0])
        if -1 in cluster_stats[0]
        else 0,
    }


def get_cluster_centroids(
    embeddings: xp.ndarray, cluster_labels: xp.ndarray
) -> Dict[int, xp.ndarray]:
    unique_labels = xp.unique(cluster_labels)
    cluster_centroids = {}
    for label in unique_labels:
        if label != -1:  # Skip noise points
            cluster_embeddings = embeddings[cluster_labels == label]
            cluster_centroid = xp.mean(cluster_embeddings, axis=0)
            cluster_centroids[label] = cluster_centroid
    return cluster_centroids
