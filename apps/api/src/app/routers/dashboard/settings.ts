import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { router, authenticatedProcedure } from '../../trpc';

export const settings = router({
  deleteEverything: authenticatedProcedure.mutation(async (opts) => {
    const { user } = opts.ctx as AppContext;

    await prisma.user.delete({
      where: { id: user.id },
    });
  }),
});
