import numpy as np
from polars import Series

weights = {
    "big5": 0.2,
    "mft": 0.1,
    "proactive_interests": 0.4,
    "reactive_interests": 0.3,
}

assert sum(weights.values()) == 1.0, "Overall match formula weights must sum to 1.0"


def calculate_overall_similarity(
    big5_similarity: np.floating,
    mft_similarity: np.floating,
    proactive_interests_similarity: np.floating,
    reactive_interests_similarity: np.floating,
) -> np.floating:
    return (
        (weights["big5"] * big5_similarity)
        + (weights["mft"] * mft_similarity)
        + (weights["proactive_interests"] * proactive_interests_similarity)
        + (weights["reactive_interests"] * reactive_interests_similarity)
    )


def calculate_interests_similarity(scores: Series):
    return _exponential_mean(scores.to_numpy())


def calculate_mft_similarity(mft1, mft2):
    return _euclidean_similarity(
        np.array(
            [
                mft1.careHarm,
                mft1.fairnessCheating,
                mft1.loyaltyBetrayal,
                mft1.authoritySubversion,
                mft1.sanctityDegradation,
            ]
        ),
        np.array(
            [
                mft2.careHarm,
                mft2.fairnessCheating,
                mft2.loyaltyBetrayal,
                mft2.authoritySubversion,
                mft2.sanctityDegradation,
            ]
        ),
    )


def calculate_big5_similarity(big5_1, big5_2):
    return _euclidean_similarity(
        np.array(
            [
                big5_1.openness,
                big5_1.conscientiousness,
                big5_1.extraversion,
                big5_1.agreeableness,
                big5_1.neuroticism,
            ]
        ),
        np.array(
            [
                big5_2.openness,
                big5_2.conscientiousness,
                big5_2.extraversion,
                big5_2.agreeableness,
                big5_2.neuroticism,
            ]
        ),
    )


def _euclidean_similarity(vec1: np.ndarray, vec2: np.ndarray) -> np.floating:
    distance = np.linalg.norm(vec1 - vec2)
    max_distance = np.linalg.norm(np.ones_like(vec1) - np.zeros_like(vec1))
    return 1 - (distance / max_distance)


def _exponential_mean(scores: np.ndarray) -> np.floating:
    return np.log(np.mean(np.exp(scores)))
