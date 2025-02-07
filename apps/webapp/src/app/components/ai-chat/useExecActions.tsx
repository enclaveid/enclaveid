import { Message } from 'ai/react';
import { useEffect, useState } from 'react';
import { parseAndExecuteActions } from '../../services/ai/causalInferenceAgent/actions';

interface UseExecActionsProps {
  messages: Message[];
  isLoading: boolean;
  setMessages: (
    messages: Message[] | ((messages: Message[]) => Message[])
  ) => void;
  reload: () => void;
}

export function useExecActions({
  messages,
  isLoading,
  setMessages,
  reload,
}: UseExecActionsProps) {
  const [performingActions, setPerformingActions] = useState(false);
  const [hasProcessedMessage, setHasProcessedMessage] = useState<string | null>(
    null
  );

  const lastAssistantMessage = messages
    ?.filter((m) => m.role === 'assistant')
    .pop()?.content;

  const isWaiting = performingActions || isLoading;

  useEffect(() => {
    if (
      lastAssistantMessage &&
      !isWaiting &&
      lastAssistantMessage !== hasProcessedMessage
    ) {
      setPerformingActions(true);
      setHasProcessedMessage(lastAssistantMessage);

      parseAndExecuteActions(lastAssistantMessage).then((actionsResults) => {
        setPerformingActions(false);

        if (actionsResults) {
          setMessages((messages) => [
            ...messages,
            {
              role: 'user',
              content: actionsResults,
              id: `action-result-${Date.now()}`,
              parts: [],
            },
          ]);
          reload();
        }
      });
    }
  }, [
    lastAssistantMessage,
    isWaiting,
    hasProcessedMessage,
    reload,
    setMessages,
  ]);

  return {
    isWaiting,
    performingActions,
  };
}
