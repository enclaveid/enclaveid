'use client';

import { Card, CardContent } from '@enclaveid/ui/card';
import { Input } from '@enclaveid/ui/input';
import { ScrollArea } from '@enclaveid/ui/scroll-area';
import { cn } from '@enclaveid/ui-utils';
import { ToolInvocation } from 'ai';
import { Message, useChat } from 'ai/react';
import { Button } from '@enclaveid/ui/button';
import { DoubleArrowRightIcon } from '@radix-ui/react-icons';

export function AiChat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({
      maxSteps: 1,
    });

  return (
    <Card className="flex flex-col w-full">
      <CardContent className="flex flex-1 flex-col gap-4 p-4">
        <ScrollArea className="flex-1 pr-4">
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

              {m.toolInvocations?.map((toolInvocation: ToolInvocation) => (
                <div
                  key={toolInvocation.toolCallId}
                  className="mt-2 text-xs text-muted-foreground"
                >
                  {'result' in toolInvocation ? (
                    <>
                      Tool {toolInvocation.toolName}: {toolInvocation.result}
                    </>
                  ) : (
                    <>Calling {toolInvocation.toolName}...</>
                  )}
                </div>
              ))}
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
        </form>
      </CardContent>
    </Card>
  );
}
