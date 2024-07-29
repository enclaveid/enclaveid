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
import { trpc } from '../utils/trpc';
import { LoadingPage } from './LoadingPage';

export function StreamChatPage() {
  const streamChatTokenQuery = trpc.private.getStreamChatToken.useQuery();

  const { token, userId } = streamChatTokenQuery.data;

  const client = useCreateChatClient({
    apiKey: import.meta.env.VITE_STREAM_CHAT_API_KEY,
    tokenOrProvider: token,
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
