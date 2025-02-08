import {
  generateId,
  generateText,
  Message,
  streamText,
  DataStreamWriter,
} from 'ai';
import { parseAndExecuteActions } from './utils';

export async function runAgentUntilComplete(
  toolCallId: string,
  query: string,
  streamWriter: DataStreamWriter,
  agentConfig: Parameters<typeof streamText>[0]
) {
  let finalResult: string | null = null;
  const messages: Message[] = [
    {
      role: 'user',
      content: query,
      id: generateId(),
    },
  ];

  while (!finalResult) {
    const result = await generateText({
      ...agentConfig,
      messages,
    });

    messages.push({
      role: 'assistant',
      content: result.text,
      id: generateId(),
    });

    // streamWriter.writeMessageAnnotation({
    //   type: 'tool-status',
    //   toolCallId,
    //   status: 'agent-action-input',
    //   message: result.text,
    //   id: generateId(),
    // });

    const { actionsResults, finalResult: newFinalResult } =
      await parseAndExecuteActions(result.text);

    finalResult = newFinalResult;

    if (actionsResults) {
      messages.push({
        role: 'user',
        content: actionsResults,
        id: generateId(),
      });

      streamWriter.writeMessageAnnotation({
        type: 'tool-status',
        toolCallId,
        message: actionsResults,
        id: generateId(),
      });
    }
  }

  return finalResult;
}
