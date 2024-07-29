import { z } from 'zod';
import { publicProcedure, router } from '../trpc';
import { AppContext } from '../context';
import { TRPCError } from '@trpc/server';
import { asymmetricDecrypt } from '../services/crypto/asymmetricNode';
import { prisma } from '@enclaveid/backend';
import { hashPassword, verifyPassword } from '../services/crypto/passwords';
import { Gender } from '@prisma/client';

export const authentication = router({
  login: publicProcedure
    .input(
      z.object({
        encryptedCredentials: z.string(),
      }),
    )
    .mutation(async (opts) => {
      const { encryptedCredentials } = opts.input;
      const { setJwtCookie } = opts.ctx as AppContext;

      const { email, password, b64SessionKey } = JSON.parse(
        await asymmetricDecrypt(encryptedCredentials),
      );

      const user = await prisma.user.findUnique({
        where: { email, confirmedAt: { not: null } },
      });

      if (!user) {
        throw new TRPCError({
          code: 'UNAUTHORIZED',
          message: 'User not found',
        });
      }

      const passwordMatch = await verifyPassword(password, user.password);

      if (!passwordMatch) {
        throw new TRPCError({
          code: 'UNAUTHORIZED',
          message: 'Invalid password',
        });
      }

      const sessionKey = Buffer.from(b64SessionKey, 'base64');

      await prisma.session.upsert({
        where: { userId: user.id },
        update: { sessionSecret: sessionKey },
        create: { userId: user.id, sessionSecret: sessionKey },
      });

      await setJwtCookie({ id: user.id });

      return user.id;
    }),
  signup: publicProcedure
    .input(
      z.object({
        encryptedCredentials: z.string(),
      }),
    )
    .mutation(async (opts) => {
      const { encryptedCredentials } = opts.input;

      const { email, password } = JSON.parse(
        await asymmetricDecrypt(encryptedCredentials),
      );

      const existingUser = await prisma.user.findUnique({
        where: {
          email,
        },
      });

      if (existingUser) {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: 'Email already in use',
        });
      }

      const user = await prisma.user.create({
        data: {
          email,
          password: await hashPassword(password),
          confirmedAt: new Date(), // TODO remove this and send confirmation email
          userTraits: {
            create: {},
          },
          // TODO
          displayName: 'test',
          gender: Gender.OT,
          geographyLat: 0.0,
          geographyLon: 0.0,
        },
      });

      return user.id;
    }),
});
