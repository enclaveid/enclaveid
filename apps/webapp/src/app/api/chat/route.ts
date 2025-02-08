import { createDataStreamResponse, streamText } from 'ai';

import { nudgingAgentConfig } from '../../services/ai/nudgingAgent/agentConfig';

export async function POST(req: Request) {
  const { messages } = await req.json();

  return createDataStreamResponse({
    execute: (dataStream) => {
      streamText({
        ...nudgingAgentConfig(dataStream),
        messages,
      }).mergeIntoDataStream(dataStream);
    },
    onError: (error) => {
      // Error messages are masked by default for security reasons.
      // If you want to expose the error message to the client, you can do so here:
      return error instanceof Error ? error.message : String(error);
    },
  });
}
