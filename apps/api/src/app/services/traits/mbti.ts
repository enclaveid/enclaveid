import { BigFivePartial, MbtiPartial } from '@enclaveid/shared';

/**
 * Roughly approximates MBTI from Big Five traits.
 * @param bigFive
 * @returns
 */
export function bigFiveToMbti(bigFive: BigFivePartial): MbtiPartial {
  // Assert that the Big Five traits are within the expected range
  Object.values(bigFive).forEach((value) => {
    if (value < 0 || value > 1) {
      throw new Error('Big Five traits must be between 0 and 1');
    }
  });

  return {
    extraversion: bigFive.extraversion > 0.5,
    sensing: bigFive.openness < 0.5,
    thinking: bigFive.agreeableness < 0.5,
    judging: bigFive.conscientiousness > 0.5,
  };
}
