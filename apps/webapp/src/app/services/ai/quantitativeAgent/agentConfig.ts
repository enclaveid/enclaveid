import { streamText } from 'ai';
import { openRouterAi } from '../openRouterAi';
import { quantitativeAgentSystemPrompt } from './systemPrompt';

export const quantitativeAgentConfig: Parameters<typeof streamText>[0] = {
  model: openRouterAi('anthropic/claude-3.5-sonnet'),
  system: quantitativeAgentSystemPrompt,
  maxTokens: 8192,
};
