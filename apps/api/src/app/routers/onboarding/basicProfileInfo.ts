import { Gender } from '@prisma/client';
import { z } from 'zod';
import { AppContext } from '../../context';
import { router, authenticatedProcedure } from '../../trpc';
import { prisma } from '@enclaveid/backend';
import { checkProfanity } from '../../services/profanityChecker';

export const basicProfileInfo = router({
  isDisplayNameAvailable: authenticatedProcedure
    .input(
      z.object({
        displayName: z.string(),
      }),
    )
    .query(async (opts) => {
      const { displayName } = opts.input;

      if (
        displayName.length < 4 ||
        displayName.length > 16 ||
        checkProfanity(displayName)
      ) {
        return false;
      }

      const user = await prisma.user.findUnique({
        where: { displayName },
      });

      return !user;
    }),
  createBasicProfileInfo: authenticatedProcedure
    .input(
      z.object({
        displayName: z.string(),
        gender: z.nativeEnum(Gender),
        geographyLat: z.number(),
        geographyLon: z.number(),
      }),
    )
    .mutation(async (opts) => {
      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      const { displayName, gender, geographyLat, geographyLon } = opts.input;

      const user = await prisma.user.update({
        where: { id: userId },
        data: {
          displayName,
          gender,
          geographyLat,
          geographyLon,
        },
      });
    }),
});
