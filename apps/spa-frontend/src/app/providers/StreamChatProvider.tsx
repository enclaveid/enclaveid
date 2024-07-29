// ChatContext.jsx
import { createContext, useContext, useEffect } from 'react';
import { useCreateChatClient } from 'stream-chat-react';
import 'stream-chat-react/dist/css/v2/index.css';
import { trpcClient } from '../utils/trpc';

const ChatContext = createContext({ client: null, userId: null });

async function tokenProvider() {
  const result = await trpcClient.query('private.getStreamChatToken', null);

  return result as string;
}

export function StreamChatProvider({ children }) {
  useEffect(() => {
    // @ts-expect-error Type '{ env: {}; }' is missing the following properties from type 'Process': stdout, stderr, stdin, openStdin, and 52 more.
    window.process = { env: {} };
  }, []);

  const userId = localStorage.getItem('userId');

  const chatClient = useCreateChatClient({
    apiKey: import.meta.env.VITE_STREAM_CHAT_API_KEY,
    tokenOrProvider: tokenProvider,
    userData: { id: userId },
  });

  return (
    <ChatContext.Provider value={{ client: chatClient, userId }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useStreamChatClient() {
  return useContext(ChatContext);
}
