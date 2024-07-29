import {
  Chat,
  Channel,
  ChannelList,
  Window,
  ChannelHeader,
  MessageList,
  MessageInput,
  Thread,
} from 'stream-chat-react';
import 'stream-chat-react/dist/css/v2/index.css';
import { LoadingPage } from './LoadingPage';
import { CommonLayout } from '../components/CommonLayout';
import { useStreamChatClient } from '../providers/StreamChatProvider';

export function StreamChatPage() {
  const { client, userId } = useStreamChatClient();

  return (
    <CommonLayout>
      {!client ? (
        <LoadingPage customMessage="Loading chat client..." />
      ) : (
        <Chat client={client}>
          <ChannelList
            sort={{ last_message_at: -1 }}
            filters={{
              members: { $in: [userId, 'ma9o'] },
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
      )}
    </CommonLayout>
  );
}
