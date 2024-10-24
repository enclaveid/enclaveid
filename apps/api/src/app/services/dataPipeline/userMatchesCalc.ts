import { BigFive, MoralFoundations } from '@prisma/client';

const weights = {
  big5: 0.2,
  mft: 0.1,
  proactive_interests: 0.4,
  reactive_interests: 0.3,
};

// Assert that weights sum to 1.0
const weightSum = Object.values(weights).reduce((a, b) => a + b, 0);
if (Math.abs(weightSum - 1.0) > 1e-6) {
  throw new Error('Overall match formula weights must sum to 1.0');
}

function euclideanSimilarity(vec1: number[], vec2: number[]): number {
  if (vec1.length !== vec2.length) {
    throw new Error('Vectors must have the same length');
  }

  const distance = Math.sqrt(
    vec1.reduce((sum, v, i) => sum + Math.pow(v - vec2[i], 2), 0),
  );

  const maxDistance = Math.sqrt(
    vec1.length * Math.pow(1 - 0, 2), // Assuming values are normalized between 0 and 1
  );

  return 1 - distance / maxDistance;
}

function exponentialMean(scores: number[]): number {
  if (scores.length === 0) {
    return 0;
  }
  return Math.log(
    scores.map(Math.exp).reduce((sum, val) => sum + val, 0) / scores.length,
  );
}

function calculateInterestsSimilarity(scores: number[]): number {
  return exponentialMean(scores);
}

function calculateMftSimilarity(
  mft1: MoralFoundations,
  mft2: MoralFoundations,
): number {
  return euclideanSimilarity(
    [
      mft1.careHarm,
      mft1.fairnessCheating,
      mft1.loyaltyBetrayal,
      mft1.authoritySubversion,
      mft1.sanctityDegradation,
    ],
    [
      mft2.careHarm,
      mft2.fairnessCheating,
      mft2.loyaltyBetrayal,
      mft2.authoritySubversion,
      mft2.sanctityDegradation,
    ],
  );
}

function calculateBigFiveSimilarity(big5_1: BigFive, big5_2: BigFive): number {
  return euclideanSimilarity(
    [
      big5_1.openness,
      big5_1.conscientiousness,
      big5_1.extraversion,
      big5_1.agreeableness,
      big5_1.neuroticism,
    ],
    [
      big5_2.openness,
      big5_2.conscientiousness,
      big5_2.extraversion,
      big5_2.agreeableness,
      big5_2.neuroticism,
    ],
  );
}

export function calculateOverallSimilarity(
  proactiveSimilarities: number[],
  reactiveSimilarities: number[],
  currentUserTraits?: {
    bigFive: BigFive;
    moralFoundations: MoralFoundations;
  },
  otherUserTraits?: {
    bigFive: BigFive;
    moralFoundations: MoralFoundations;
  },
): number {
  const big5Similarity =
    currentUserTraits?.bigFive && otherUserTraits?.bigFive
      ? calculateBigFiveSimilarity(
          currentUserTraits.bigFive,
          otherUserTraits.bigFive,
        )
      : 0;
  const mftSimilarity =
    currentUserTraits?.moralFoundations && otherUserTraits?.moralFoundations
      ? calculateMftSimilarity(
          currentUserTraits.moralFoundations,
          otherUserTraits.moralFoundations,
        )
      : 0;
  const proactiveInterestsSimilarity = calculateInterestsSimilarity(
    proactiveSimilarities,
  );
  const reactiveInterestsSimilarity =
    calculateInterestsSimilarity(reactiveSimilarities);

  return (
    weights.big5 * big5Similarity +
    weights.mft * mftSimilarity +
    weights.proactive_interests * proactiveInterestsSimilarity +
    weights.reactive_interests * reactiveInterestsSimilarity
  );
}
