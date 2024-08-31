import { BigFivePartial, MbtiPartial } from '@enclaveid/shared';

/**
 * Roughly approximates MBTI from Big Five traits.
 * @param bigFive
 * @returns
 */
export function bigFiveToMbti(bigFive: BigFivePartial): MbtiPartial {
  return {
    extraversion: bigFive.extraversion > 0.5,
    sensing: bigFive.openness < 0.5,
    thinking: bigFive.agreeableness < 0.5,
    judging: bigFive.conscientiousness > 0.5,
  };
}
