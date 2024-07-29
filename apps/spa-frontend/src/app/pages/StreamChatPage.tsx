import {
  Chat,
  Channel,
  ChannelList,
  Window,
  ChannelHeader,
  MessageList,
  MessageInput,
  Thread,
  useCreateChatClient,
} from 'stream-chat-react';
import 'stream-chat-react/dist/css/v2/index.css';
import { trpcClient } from '../utils/trpc';
import { LoadingPage } from './LoadingPage';
import { useEffect } from 'react';

async function tokenProvider() {
  const result = await trpcClient.query('private.getStreamChatToken', null);

  return result as string;
}

export function StreamChatPage() {
  useEffect(() => {
    // @ts-expect-error Type '{ env: {}; }' is missing the following properties from type 'Process': stdout, stderr, stdin, openStdin, and 52 more.
    window.process = { env: {} };
  }, []);

  const userId = localStorage.getItem('userId');

  const client = useCreateChatClient({
    apiKey: import.meta.env.VITE_STREAM_CHAT_API_KEY,
    tokenOrProvider: tokenProvider,
    userData: { id: userId },
  });

  return !client ? (
    <LoadingPage />
  ) : (
    <Chat client={client}>
      <ChannelList
        sort={{ last_message_at: -1 }}
        filters={{
          members: { $in: [userId] },
          type: 'messaging',
        }}
        options={{ presence: true, state: true }}
      />
      <Channel>
        <Window>
          <ChannelHeader />
          <MessageList />
          <MessageInput />
        </Window>
        <Thread />
      </Channel>
    </Chat>
  );
}
