import { z } from 'zod';
import { AppContext } from '../context';
import { router, authenticatedProcedure } from '../trpc';
import { generateSasUrl } from '../services/azure/streamingUpload';
import { DataProvider } from '@enclaveid/shared';

export const fileUpload = router({
  getUploadUrl: authenticatedProcedure
    .input(z.object({ dataProvider: z.nativeEnum(DataProvider) }))
    .query(async ({ ctx, input }) => {
      const {
        user: { id: userId },
      } = ctx as AppContext;

      const { dataProvider } = input;

      return { url: await generateSasUrl(dataProvider, userId) };
    }),
});
