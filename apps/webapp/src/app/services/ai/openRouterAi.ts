import { createOpenRouter } from '@openrouter/ai-sdk-provider';

export const openRouterAi = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY!,
});
