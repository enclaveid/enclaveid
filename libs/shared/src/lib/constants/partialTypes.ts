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

const mbti = Prisma.validator<Prisma.MbtiDefaultArgs>()({
  select: {
    extraversion: true,
    judging: true,
    thinking: true,
    sensing: true,
  },
});

export type MbtiPartial = Prisma.MbtiGetPayload<typeof mbti>;
