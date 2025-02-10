import numpy as np


def pad_vectors(vectors: np.ndarray, target_dim: int = 2000) -> list[list[float]]:
    res = []
    if vectors.shape[1] >= target_dim:
        res = vectors[:, :target_dim].astype(np.float64).tolist()
    else:
        padding_width = ((0, 0), (0, target_dim - vectors.shape[1]))
        padded = np.pad(vectors, padding_width, mode="constant", constant_values=0)
        res = padded.astype(np.float64).tolist()

    return res  # type: ignore
