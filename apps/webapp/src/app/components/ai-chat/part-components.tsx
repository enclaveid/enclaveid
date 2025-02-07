import {
  ReasoningUIPart,
  TextUIPart,
  ToolInvocationUIPart,
} from '@ai-sdk/ui-utils';

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
