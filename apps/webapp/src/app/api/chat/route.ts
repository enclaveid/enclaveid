import { streamText } from 'ai';
import { openRouterAi } from '../../services/ai/openRouterAi';
import { LanguageModelV1 } from '@ai-sdk/provider';
import { systemPrompt } from '../../services/ai/causalInferenceAgent/systemPrompt';
// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openRouterAi(
      //'google/gemini-2.0-flash-thinking-exp:free'
      'deepseek/deepseek-r1'
      //'google/gemini-2.0-flash-001'
      //'anthropic/claude-3.5-sonnet'
    ) as LanguageModelV1,
    messages,
    maxTokens: 8192,
    system: systemPrompt,
    // TODO: tool use is a bit broken atm
    // tools: [...actions]
  });

  return result.toDataStreamResponse({
    sendReasoning: true,
  });
}
