from typing import Dict

import numpy as np


def get_cluster_stats(cluster_labels: np.ndarray, prefix="") -> Dict[str, int]:
    cluster_stats = np.unique(cluster_labels, return_counts=True)
    return {
        f"{prefix}clusters_count": len(cluster_stats[0]),
        f"{prefix}noise_count": int(cluster_stats[1][0])
        if -1 in cluster_stats[0]
        else 0,
    }
