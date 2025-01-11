import type { NextApiRequest, NextApiResponse } from 'next';
import NextAuth from 'next-auth';
import GithubProvider from 'next-auth/providers/github';

export default async function auth(req: NextApiRequest, res: NextApiResponse) {
  return await NextAuth(req, res, {
    providers: [
      GithubProvider({
        clientId: process.env.GITHUB_CLIENT_ID!,
        clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      }),
      // EmailProvider({
      //   sendVerificationRequest: async ({
      //     expires,
      //     token,
      //     identifier,
      //     url,
      //     provider,
      //     theme,
      //   }) => {
      //     await sendEmail(identifier, 'Confirm your email', url);
      //   },
      // }),
    ],
  });
}
