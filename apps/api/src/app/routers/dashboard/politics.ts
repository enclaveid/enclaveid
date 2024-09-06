import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { authenticatedProcedure, router } from '../../trpc';
import { z } from 'zod';

export const politics = router({
  getPoliticsTraits: authenticatedProcedure
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
              politicalCompass: {
                select: {
                  economic: true,
                  social: true,
                },
                orderBy: {
                  createdAt: 'desc',
                },
                take: 1,
              },
              moralFoundations: {
                select: {
                  careHarm: true,
                  fairnessCheating: true,
                  authoritySubversion: true,
                  loyaltyBetrayal: true,
                  sanctityDegradation: true,
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
        politicalCompass: user?.userTraits?.politicalCompass[0],
        moralFoundations: user?.userTraits?.moralFoundations[0],
      };
    }),
});
