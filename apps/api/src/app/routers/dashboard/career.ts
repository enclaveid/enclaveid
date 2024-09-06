import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { authenticatedProcedure, router } from '../../trpc';
import { z } from 'zod';

export const career = router({
  getCareerTraits: authenticatedProcedure
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
              riasec: {
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
        riasec: user?.userTraits?.riasec[0],
      };
    }),
});
