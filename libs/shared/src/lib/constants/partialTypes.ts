import { Prisma } from '@prisma/client';

const bigFive = Prisma.validator<Prisma.BigFiveDefaultArgs>()({
  select: {
    extraversion: true,
    agreeableness: true,
    conscientiousness: true,
    neuroticism: true,
    openness: true,
  },
});

export type BigFivePartial = Prisma.BigFiveGetPayload<typeof bigFive>;

const mbti = Prisma.validator<Prisma.MbtiDefaultArgs>()({
  select: {
    extraversion: true,
    judging: true,
    thinking: true,
    sensing: true,
  },
});

export type MbtiPartial = Prisma.MbtiGetPayload<typeof mbti>;

const moralFoundations = Prisma.validator<Prisma.MoralFoundationsDefaultArgs>()(
  {
    select: {
      careHarm: true,
      fairnessCheating: true,
      loyaltyBetrayal: true,
      authoritySubversion: true,
      sanctityDegradation: true,
      goodCheck: true,
      mathCheck: true,
    },
  },
);

export type MoralFoundationsPartial = Prisma.MoralFoundationsGetPayload<
  typeof moralFoundations
>;

const politicalCompass = Prisma.validator<Prisma.PoliticalCompassDefaultArgs>()(
  {
    select: {
      economic: true,
      social: true,
    },
  },
);

export type PoliticalCompassPartial = Prisma.PoliticalCompassGetPayload<
  typeof politicalCompass
>;

const sixteenPersonalityFactor =
  Prisma.validator<Prisma.SixteenPersonalityFactorDefaultArgs>()({
    select: {
      reasoning: true,
      emotionalStability: true,
      dominance: true,
      liveliness: true,
      ruleConsciousness: true,
      socialBoldness: true,
      sensitivity: true,
      vigilance: true,
      abstractedness: true,
      privateness: true,
      apprehension: true,
      opennessToChange: true,
      selfReliance: true,
      perfectionism: true,
      tension: true,
    },
  });

export type SixteenPersonalityFactorPartial =
  Prisma.SixteenPersonalityFactorGetPayload<typeof sixteenPersonalityFactor>;
