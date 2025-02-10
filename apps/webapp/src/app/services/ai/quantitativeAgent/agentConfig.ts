import { streamText } from 'ai';
import { quantitativeAgentSystemPrompt } from './systemPrompt';
import { anthropic } from '@ai-sdk/anthropic';

export const quantitativeAgentConfig: Parameters<typeof streamText>[0] = {
  model: anthropic('claude-3-5-sonnet-20241022'),
  system: quantitativeAgentSystemPrompt,
  maxTokens: 8192,
};
