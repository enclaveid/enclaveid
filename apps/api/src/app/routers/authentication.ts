import { z } from 'zod';
import { publicProcedure, router } from '../trpc';
import { AppContext } from '../context';
import { TRPCError } from '@trpc/server';
import { asymmetricDecrypt } from '../services/crypto/asymmetricNode';
import { prisma } from '@enclaveid/backend';
import { hashPassword, verifyPassword } from '../services/crypto/passwords';
import { checkProfanity, checkEmail } from '../services/userInputValidation';
import { sendEmail } from '../services/azure/mailer';

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
      const { setJwtCookie } = opts.ctx as AppContext;

      const { encryptedCredentials } = opts.input;

      const { email, password, displayName, country, gender } = JSON.parse(
        await asymmetricDecrypt(encryptedCredentials),
      );

      if (process.env.WHITELIST_ENABLED === 'true') {
        const whitelistedEmail = await prisma.whitelistedEmail.findUnique({
          where: { email },
        });

        if (!whitelistedEmail) {
          throw new TRPCError({
            code: 'UNAUTHORIZED',
            message: 'Email not whitelisted',
          });
        }
      }

      const user = await prisma.user.create({
        data: {
          email,
          password: await hashPassword(password),
          displayName,
          gender,
          country,
        },
      });

      try {
        sendEmail(
          email,
          'Confirm your email address',
          `
        <html>
          <body>
            <p>Welcome to EnclaveID. Please confirm your email address by clicking the link below:</p>
            <p>
              <a href="${process.env.FRONTEND_URL}/confirm-email?token=${user.confirmationCode}" target="_blank" style="color: #007bff; text-decoration: underline;">
                ${process.env.FRONTEND_URL}/confirm-email?token=${user.confirmationCode}
              </a>
            </p>
            <p>If you did not sign up for EnclaveID, you can ignore this email.</p>
          </body>
        </html>
        `,
        );
      } catch (err) {
        console.error(err);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Error sending email',
        });
      }

      await setJwtCookie({ id: user.id });

      return user.id;
    }),
  isDisplayNameAvailable: publicProcedure
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
  isEmailAvailable: publicProcedure
    .input(
      z.object({
        email: z.string(),
      }),
    )
    .query(async (opts) => {
      const { email } = opts.input;

      if (!checkEmail(email)) {
        return false;
      }

      const user = await prisma.user.findUnique({
        where: { email },
      });

      return !user;
    }),
});
