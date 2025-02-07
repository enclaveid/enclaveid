'use client';

import { Card, CardContent } from '@enclaveid/ui/card';
import { Input } from '@enclaveid/ui/input';
import { ScrollArea } from '@enclaveid/ui/scroll-area';
import { cn } from '@enclaveid/ui-utils';
import { Message, useChat } from 'ai/react';
import { Button } from '@enclaveid/ui/button';
import { DoubleArrowRightIcon } from '@radix-ui/react-icons';
import { useRef } from 'react';
import { ReasoningUIPart, ToolInvocationUIPart } from '@ai-sdk/ui-utils';
import { ReasoningPartComponent } from './part-components';
import { ToolInvocationPartComponent } from './part-components';
import { useExecActions } from './useExecActions';

export function AiChat() {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    setMessages,
    reload,
  } = useChat({
    maxSteps: 1,
  });

  const buttonRef = useRef<HTMLButtonElement>(null);

  const { isWaiting } = useExecActions({
    messages,
    isLoading,
    setMessages,
    reload,
  });

  return (
    <Card className="h-full w-full">
      <CardContent className="flex flex-col gap-4 p-4 h-full">
        <ScrollArea className="flex-1 pr-4 overflow-y-auto">
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

              {m.parts?.map((part, index) => {
                const componentKey = `${m.id}-part-${index}`;
                return {
                  'tool-invocation': (
                    <ToolInvocationPartComponent
                      key={componentKey}
                      toolInvocationPart={part as ToolInvocationUIPart}
                    />
                  ),
                  reasoning: (
                    <ReasoningPartComponent
                      key={componentKey}
                      reasoningPart={part as ReasoningUIPart}
                    />
                  ),
                  text: <div key={componentKey}></div>,
                }[part.type];
              })}
            </div>
          ))}

          {isWaiting && (
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
        </ScrollArea>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={handleInputChange}
            placeholder="Type a message..."
            className="flex-1"
            disabled={isWaiting}
          />
          <Button type="submit" disabled={isWaiting} ref={buttonRef}>
            <DoubleArrowRightIcon />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
