import { prisma } from '@enclaveid/backend';
import { AppContext } from '../context';
import { router, authenticatedProcedure } from '../trpc';
import { getTipiScores } from '../services/traits/bigFive';
import { z } from 'zod';
import { getMfq20Scores } from '../services/traits/moralFoundations';
import { Purpose } from '@prisma/client';
import { bigFiveToMbti } from '../services/traits/mbti';
import { politicalCompassFromMoralFoundations } from '../services/traits/politicalCompass';

export const updateUser = router({
  createbigFive: authenticatedProcedure
    .input(
      z.object({
        answers: z.record(z.string(), z.string()),
      }),
    )
    .mutation(async (opts) => {
      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      const { answers } = opts.input;

      const bigFiveScores = getTipiScores(answers);

      await prisma.bigFive.create({
        data: {
          ...bigFiveScores,
          userTraits: {
            connectOrCreate: {
              where: {
                userId,
              },
              create: {
                userId,
              },
            },
          },
        },
      });

      // TODO: We also approximate MBTI but we should infer it properly
      const mbtiScores = bigFiveToMbti(bigFiveScores);

      await prisma.mbti.create({
        data: {
          ...mbtiScores,
          userTraits: {
            connectOrCreate: {
              where: {
                userId,
              },
              create: {
                userId,
              },
            },
          },
        },
      });
    }),
  createMoralFoundations: authenticatedProcedure
    .input(
      z.object({
        answers: z.record(z.string(), z.string()),
      }),
    )
    .mutation(async (opts) => {
      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      const { answers } = opts.input;

      const mftScores = getMfq20Scores(answers);

      await prisma.moralFoundations.create({
        data: {
          ...mftScores,
          userTraits: {
            connectOrCreate: {
              where: {
                userId,
              },
              create: {
                userId,
              },
            },
          },
        },
      });

      // TODO: We also approximate political orientation but we should infer it properly
      const politicalCompassScores =
        politicalCompassFromMoralFoundations(mftScores);

      await prisma.politicalCompass.create({
        data: {
          ...politicalCompassScores,
          userTraits: {
            connectOrCreate: {
              where: {
                userId,
              },
              create: {
                userId,
              },
            },
          },
        },
      });
    }),
  deleteEverything: authenticatedProcedure.mutation(async (opts) => {
    const { user } = opts.ctx as AppContext;

    await prisma.user.delete({
      where: { id: user.id },
    });
  }),
  updatePurposes: authenticatedProcedure
    .input(
      z.object({
        purposes: z.array(z.nativeEnum(Purpose)),
      }),
    )
    .mutation(async (opts) => {
      const { user } = opts.ctx as AppContext;

      await prisma.user.update({
        where: { id: user.id },
        data: {
          purposes: opts.input.purposes,
        },
      });
    }),
});
