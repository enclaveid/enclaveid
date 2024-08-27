import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { router, authenticatedProcedure } from '../../trpc';
import { TRPCError } from '@trpc/server';
import { z } from 'zod';

export const emailConfirmation = router({
  confirmEmail: authenticatedProcedure
    .input(
      z.object({
        token: z.string(),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      const {
        user: { id: userId },
      } = ctx as AppContext;

      const { token } = input;

      const user = await prisma.user.findUnique({
        where: { id: userId, confirmationCode: token },
      });

      if (!user) {
        throw new TRPCError({
          code: 'NOT_FOUND',
          message: 'User not found',
        });
      }

      await prisma.user.update({
        where: { id: userId },
        data: { confirmedAt: new Date() },
      });
    }),
});
