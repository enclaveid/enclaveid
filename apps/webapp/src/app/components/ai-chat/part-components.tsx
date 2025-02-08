import {
  JSONValue,
  ReasoningUIPart,
  TextUIPart,
  ToolInvocationUIPart,
} from '@ai-sdk/ui-utils';
import { ChevronDown } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@enclaveid/ui/collapsible';

export function IntermediateAgentActionsComponent({
  data,
}: {
  data: JSONValue[] | undefined;
}) {
  if (!data) {
    return null;
  }

  return (
    <Collapsible>
      <CollapsibleTrigger className="flex w-full items-center gap-2 text-xs text-muted-foreground hover:text-foreground">
        <ChevronDown className="h-4 w-4" />
        <span>Intermediate Tool Calls</span>
      </CollapsibleTrigger>
      <CollapsibleContent>
        {data.map((record) => (
          <div
            key={(record as { id: string }).id}
            className="mt-2 text-xs text-muted-foreground pl-6"
          >
            {(record as { message: string }).message}
          </div>
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}

export function ToolInvocationPartComponent({
  toolInvocationPart,
}: {
  toolInvocationPart: ToolInvocationUIPart;
}) {
  const { toolInvocation } = toolInvocationPart;

  return (
    <div
      key={toolInvocation.toolCallId}
      className="mt-2 text-xs text-muted-foreground"
    >
      {'result' in toolInvocation ? (
        <>
          Tool {toolInvocation.toolName}:{' '}
          {JSON.stringify(toolInvocation.result, null, 2)}
        </>
      ) : (
        <>
          Calling {toolInvocation.toolName} with{' '}
          {JSON.stringify(toolInvocation.args, null, 2)}
        </>
      )}
    </div>
  );
}

export function ReasoningPartComponent({
  reasoningPart,
}: {
  reasoningPart: ReasoningUIPart;
}) {
  return (
    <div className="mt-2 text-xs text-muted-foreground">
      {reasoningPart.reasoning}
    </div>
  );
}

export function TextPartComponent({ textPart }: { textPart: TextUIPart }) {
  return (
    <div className="mt-2 text-xs text-muted-foreground">{textPart.text}</div>
  );
}
