import { prisma } from '@enclaveid/backend';
import { authenticatedProcedure, router } from '../trpc';
import { AppContext } from '../context';
import { z } from 'zod';
import { createExportZip } from '../services/azure/createExportZip';

export const settings = router({
  getSettings: authenticatedProcedure.query(async (opts) => {
    const {
      user: { id: userId },
    } = opts.ctx as AppContext;

    return await prisma.user.findUnique({
      where: {
        id: userId,
      },
      select: {
        matchingEnabled: true,
        sensitiveMatchingEnabled: true,
      },
    });
  }),
  updateSettings: authenticatedProcedure
    .input(
      z.object({
        matchingEnabled: z.boolean().optional(),
        sensitiveMatchingEnabled: z.boolean().optional(),
      }),
    )
    .mutation(async (opts) => {
      const { user } = opts.ctx as AppContext;

      await prisma.user.update({
        where: { id: user.id },
        data: opts.input,
      });
    }),
  deleteEverything: authenticatedProcedure.mutation(async (opts) => {
    const { user } = opts.ctx as AppContext;

    await prisma.user.delete({
      where: { id: user.id },
    });
  }),
  downloadData: authenticatedProcedure.mutation(async (opts) => {
    const { user } = opts.ctx as AppContext;

    return await createExportZip(user.id);
  }),
});
