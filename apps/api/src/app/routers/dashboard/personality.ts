import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { authenticatedProcedure, router } from '../../trpc';
import {
  BigFivePartial,
  MbtiPartial,
  SixteenPersonalityFactorPartial,
} from '@enclaveid/shared';
import { z } from 'zod';

export const personality = router({
  getPersonalityTraits: authenticatedProcedure
    .input(
      z
        .object({
          userId: z.string(),
        })
        .optional(),
    )
    .query(async (opts) => {
      const {
        user: { id: currentUserId },
      } = opts.ctx as AppContext;

      const userId = opts.input?.userId || currentUserId;

      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
          userTraits: {
            include: {
              bigFive: {
                select: {
                  extraversion: true,
                  agreeableness: true,
                  conscientiousness: true,
                  neuroticism: true,
                  openness: true,
                },
                orderBy: {
                  createdAt: 'desc',
                },
                take: 1,
              },
              sixteenPersonalityFactor: {
                select: {
                  warmth: true,
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
                orderBy: {
                  createdAt: 'desc',
                },
                take: 1,
              },
              mbti: {
                select: {
                  extraversion: true,
                  sensing: true,
                  thinking: true,
                  judging: true,
                },
                orderBy: {
                  createdAt: 'desc',
                },
                take: 1,
              },
            },
          },
        },
      });

      return {
        bigfive: user?.userTraits?.bigFive[0],
        sixteenPersonalityFactor: user?.userTraits?.sixteenPersonalityFactor[0],
        mbti: user?.userTraits?.mbti[0],
      } as {
        bigfive: BigFivePartial;
        sixteenPersonalityFactor: SixteenPersonalityFactorPartial;
        mbti: MbtiPartial;
      };
    }),
});
