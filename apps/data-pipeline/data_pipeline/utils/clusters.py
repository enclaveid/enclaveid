from typing import Dict, List

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


def get_soft_transitions(
    membership_vectors: xp.ndarray, top_k: int = 5, skip_top: int = 0
) -> List[List[Dict[str, float]]]:
    """
    For each sample, find the top k clusters with highest membership probability,
    optionally skipping the highest probability clusters

    Parameters:
    membership_vectors : numpy.ndarray (n_samples, n_clusters)
        Probability of each sample belonging to each cluster
    top_k : int, default=5
        Number of clusters to return for each sample
    skip_top : int, default=1
        Number of highest probability clusters to skip. Can be 0 to include all top clusters.

    Returns:
    list of lists
        For each sample, returns list of dicts with cluster_id and probability
        for the top k clusters after skipping the specified number of highest clusters
    """
    n_samples = membership_vectors.shape[0]

    # Validate inputs
    if skip_top < 0:
        raise ValueError("skip_top must be non-negative")
    if skip_top + top_k > membership_vectors.shape[1]:
        raise ValueError("skip_top + top_k cannot exceed number of clusters")

    # Initialize output array
    soft_transitions = []

    for i in range(n_samples):
        # Get probabilities for current sample
        probs = membership_vectors[i]

        # Get indices sorted by probability (ascending)
        sorted_indices = xp.argsort(probs)

        # If skip_top is 0, just take the top k indices
        # Otherwise, skip the specified number and take the next k
        if skip_top == 0:
            selected_indices = sorted_indices[-top_k:][::-1]
        else:
            selected_indices = sorted_indices[-(skip_top + top_k) : -skip_top][::-1]

        # Create list of dictionaries for this sample
        sample_transitions = [
            dict(cluster_id=int(cluster_id), probability=float(probs[cluster_id]))
            for cluster_id in selected_indices
        ]

        soft_transitions.append(sample_transitions)

    return soft_transitions
