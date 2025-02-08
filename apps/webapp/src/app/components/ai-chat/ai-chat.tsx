'use client';

import { Card, CardContent } from '@enclaveid/ui/card';
import { Input } from '@enclaveid/ui/input';
import { ScrollArea } from '@enclaveid/ui/scroll-area';
import { cn } from '@enclaveid/ui-utils';
import { Message, useChat } from 'ai/react';
import { Button } from '@enclaveid/ui/button';
import { DoubleArrowRightIcon, ReloadIcon } from '@radix-ui/react-icons';
import { ReasoningUIPart, ToolInvocationUIPart } from '@ai-sdk/ui-utils';
import {
  IntermediateAgentActionsComponent,
  ReasoningPartComponent,
} from './part-components';
import { ToolInvocationPartComponent } from './part-components';

export function AiChat() {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    reload,
  } = useChat({
    maxSteps: 2,
  });

  return (
    <Card className="h-full w-full">
      <CardContent className="flex flex-col gap-4 p-4 h-full">
        <ScrollArea className="h-[600px] pr-4 overflow-y-auto">
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
          <Button type="button" onClick={() => reload()} variant="outline">
            <ReloadIcon />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
