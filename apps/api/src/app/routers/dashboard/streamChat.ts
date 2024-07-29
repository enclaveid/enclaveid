import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { authenticatedProcedure, router } from '../../trpc';
import { StreamChat } from 'stream-chat';

const streamChatClient = new StreamChat(
  process.env.STREAM_CHAT_API_KEY,
  process.env.STREAM_CHAT_API_SECRET,
);

export const streamChat = router({
  getStreamChatToken: authenticatedProcedure.query(async (opts) => {
    const {
      user: { id: userId },
    } = opts.ctx as AppContext;

    // If user doesn't have a token we create a new one. Tokens are valid forever.
    const user =
      (await prisma.user.findUnique({
        where: { id: userId, streamChatToken: { not: null } },
      })) ??
      (await prisma.user.update({
        where: { id: userId },
        data: {
          streamChatToken: streamChatClient.createToken(userId),
        },
      }));

    return {
      userId,
      token: user.streamChatToken,
    };
  }),
});
