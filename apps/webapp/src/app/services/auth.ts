import NextAuth from 'next-auth';
import GithubProvider from 'next-auth/providers/github';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from './db/prisma';
import { sendEmail } from './sendEmail';
import Nodemailer from 'next-auth/providers/nodemailer';

export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: PrismaAdapter(prisma),
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
