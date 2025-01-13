import NextAuth from 'next-auth';
import GithubProvider from 'next-auth/providers/github';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '../../../services/db/prisma';
import EmailProvider from 'next-auth/providers/email';
import { sendEmail } from '../../../services/sendEmail';
const handler = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    EmailProvider({
      sendVerificationRequest: async ({ identifier: email, url }) => {
        await sendEmail(email, 'Verify your email', url);
      },
    }),
  ],
});

export { handler as GET, handler as POST };
