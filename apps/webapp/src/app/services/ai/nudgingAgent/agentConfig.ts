import { streamText } from 'ai';
import { openRouterAi } from '../openRouterAi';
import { nudgingAgentSystemPrompt } from './systemPrompt';

export const nudgingAgentConfig: Parameters<typeof streamText>[0] = {
  model: openRouterAi('anthropic/claude-3.5-sonnet'),
  system: nudgingAgentSystemPrompt,
  maxTokens: 8192,
  
};
