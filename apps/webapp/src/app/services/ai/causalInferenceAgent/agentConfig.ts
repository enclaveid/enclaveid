import { streamText } from 'ai';
import { openRouterAi } from '../openRouterAi';
import { causalInferenceAgentSystemPrompt } from './systemPrompt';

export const causalInferenceAgentConfig: Parameters<typeof streamText>[0] = {
  model: openRouterAi('anthropic/claude-3.5-sonnet'),
  system: causalInferenceAgentSystemPrompt,
  maxTokens: 8192,
};
