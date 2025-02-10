'use client';

import { Card, CardContent } from '@enclaveid/ui/card';
import { Input } from '@enclaveid/ui/input';
import { ScrollArea } from '@enclaveid/ui/scroll-area';
import { cn } from '@enclaveid/ui-utils';
import { Message, useChat } from 'ai/react';
import { Button } from '@enclaveid/ui/button';
import { DoubleArrowRightIcon, ReloadIcon } from '@radix-ui/react-icons';
import {
  IntermediateAgentActionsComponent,
  ToolResultsPartsComponent,
} from './part-components';
import { useCallback, useState } from 'react';
import { generateId, ToolInvocationUIPart } from '@ai-sdk/ui-utils';

export function AiChat() {
  const [suggestions, setSuggestions] = useState<{
    horizontal: string[];
    vertical: string[];
  }>({
    horizontal: [],
    vertical: [],
  });

  const {
    messages,
    setMessages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    reload,
  } = useChat({
    maxSteps: 2,
    onToolCall: async ({ toolCall }) => {
      if (toolCall.toolName === 'suggestNextQuestions') {
        setSuggestions(
          toolCall.args as { horizontal: string[]; vertical: string[] }
        );
      }
      return { toolCall };
    },
  });

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: 'user',
          content: suggestion,
          parts: [],
        },
      ]);
      reload();
    },
    [setMessages, reload]
  );

  return (
    <Card className="h-full w-full">
      <CardContent className="flex flex-col gap-4 p-4 h-full">
        <ScrollArea className="flex-1 pr-4 overflow-y-auto">
          <div className="flex flex-col gap-4">
            {messages?.map((m: Message) => (
              <div
                key={m.id}
                className={cn('mb-4 flex flex-col', {
                  'items-end': m.role === 'user',
                })}
              >
                <div
                  className={cn('rounded-lg px-3 py-2 text-sm', {
                    'bg-primary text-primary-foreground': m.role === 'user',
                    'bg-muted': m.role === 'assistant',
                  })}
                >
                  {m.content}
                </div>

                <IntermediateAgentActionsComponent data={m.annotations} />

                <ToolResultsPartsComponent
                  messageId={m.id}
                  parts={
                    m.parts?.filter(
                      (p) => p.type === 'tool-invocation'
                    ) as ToolInvocationUIPart[]
                  }
                />
              </div>
            ))}

            {isLoading && (
              <div className="mb-4 flex flex-col">
                <div className="bg-muted rounded-lg px-3 py-2 text-sm w-fit">
                  <span className="inline-flex gap-1">
                    <span className="animate-bounce">.</span>
                    <span className="animate-bounce [animation-delay:0.2s]">
                      .
                    </span>
                    <span className="animate-bounce [animation-delay:0.4s]">
                      .
                    </span>
                  </span>
                </div>
              </div>
            )}

            {suggestions.horizontal.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="text-sm font-medium text-muted-foreground">
                  Follow-up questions:
                </div>
                <div className="flex flex-wrap gap-2">
                  {suggestions.horizontal.map((suggestion, index) => (
                    <Button
                      key={`horizontal-${index}`}
                      variant="outline"
                      size="sm"
                      color="blue"
                      onClick={() => handleSuggestionClick(suggestion)}
                      disabled={isLoading}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {suggestions.vertical.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="text-sm font-medium text-muted-foreground">
                  Related topics:
                </div>
                <div className="flex flex-wrap gap-2">
                  {suggestions.vertical.map((suggestion, index) => (
                    <Button
                      key={`vertical-${index}`}
                      variant="outline"
                      size="sm"
                      color="red"
                      onClick={() => handleSuggestionClick(suggestion)}
                      disabled={isLoading}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={handleInputChange}
            placeholder="Type a message..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading}>
            <DoubleArrowRightIcon />
          </Button>

        </form>
      </CardContent>
    </Card>
  );
}
