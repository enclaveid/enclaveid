import {
  MoralFoundationsPartial,
  PoliticalCompassPartial,
} from '@enclaveid/shared';

/**
 * Roughly approximates the political compass from moral foundations.
 * @param moralFoundations
 * @returns
 */
export function politicalCompassFromMoralFoundations(
  moralFoundations: MoralFoundationsPartial,
): PoliticalCompassPartial {
  // Assert that the Moral Foundations traits are within the expected range
  Object.values(moralFoundations).forEach((value) => {
    if (value < 0 || value > 1) {
      throw new Error('Moral Foundations traits must be between 0 and 1');
    }
  });

  const {
    careHarm,
    fairnessCheating,
    loyaltyBetrayal,
    authoritySubversion,
    sanctityDegradation,
  } = moralFoundations;

  // Calculate economic axis
  // Left (-1) to Right (1)
  const economicAxis =
    (loyaltyBetrayal + authoritySubversion + sanctityDegradation) / 3 -
    (careHarm + fairnessCheating) / 2;

  // Calculate authoritarian axis
  // Libertarian (-1) to Authoritarian (1)
  const authoritarianAxis =
    (loyaltyBetrayal + authoritySubversion + sanctityDegradation) / 3;

  return {
    economic: economicAxis * 2 - 1, // Scale to -1 to 1
    social: authoritarianAxis * 2 - 1, // Scale to -1 to 1
  };
}
