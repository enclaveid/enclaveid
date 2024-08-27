import { prisma } from '@enclaveid/backend';
import { AppContext } from '../context';
import { router, authenticatedProcedure } from '../trpc';
import { getTipiScores } from '../services/traits/bigFive';
import { z } from 'zod';
import { getMfq20Scores } from '../services/traits/moralFoundations';
import { Purpose } from '@prisma/client';

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

      const normalizedScores = getTipiScores(answers);

      return await prisma.bigFive.create({
        data: {
          ...normalizedScores,
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

      const normalizedScores = getMfq20Scores(answers);

      return await prisma.moralFoundations.create({
        data: {
          ...normalizedScores,
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
