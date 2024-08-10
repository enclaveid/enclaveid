import { prisma } from '@enclaveid/backend';
import { AppContext } from '../context';
import { authenticatedProcedure, router } from '../trpc';
import { TRPCError } from '@trpc/server';

export const authUtils = router({
  authCheck: authenticatedProcedure.query(async () => {
    // We always return true since authentication is handled upstream
    return { isAuthenticated: true };
  }),
  logout: authenticatedProcedure.mutation(async (opts) => {
    const {
      setJwtCookie,
      user: { id: userId },
    } = opts.ctx as AppContext;

    return await prisma.session
      .delete({
        where: { userId },
      })
      .then(() => {
        setJwtCookie({ id: null });
        return { success: true };
      })
      .catch(() => {
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to log out',
        });
      });
  }),
});
