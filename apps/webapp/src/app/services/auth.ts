import NextAuth from 'next-auth';
import GithubProvider from 'next-auth/providers/github';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from './db/prisma';
import { sendEmail } from './sendEmail';
import Nodemailer from 'next-auth/providers/nodemailer';
import { PrismaClient } from '@prisma/client';
import { Adapter } from 'next-auth/adapters';

// fix: Record to delete does not exist. https://github.com/nextauthjs/next-auth/issues/4495
function CustomPrismaAdapter(p: PrismaClient): Adapter {
  const origin = PrismaAdapter(p);
  return {
    ...origin,
    deleteSession: async (sessionToken: string) => {
      try {
        return await p.session.deleteMany({ where: { sessionToken } });
      } catch (e) {
        console.error('Failed to delete session', e);
        return null;
      }
    },
  } as unknown as Adapter;
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: CustomPrismaAdapter(prisma),
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    Nodemailer({
      server: process.env.AZURE_EMAIL_CONNECTION_STRING!,
      sendVerificationRequest: async ({ identifier: email, url }) => {
        await sendEmail(email, 'Verify your email', url);
      },
    }),
  ],
});
