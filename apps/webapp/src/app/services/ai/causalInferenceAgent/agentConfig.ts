import { streamText } from 'ai';
import { causalInferenceAgentSystemPrompt } from './systemPrompt';
import { anthropic } from '@ai-sdk/anthropic';

export const causalInferenceAgentConfig: Parameters<typeof streamText>[0] = {
  model: anthropic('claude-3-5-sonnet-20241022'),
  system: causalInferenceAgentSystemPrompt,
  maxTokens: 8192,
};
