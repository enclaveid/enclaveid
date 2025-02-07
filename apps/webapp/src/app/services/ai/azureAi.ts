import { createAzure } from '@ai-sdk/azure';

export const azureAi = createAzure({
  apiKey: process.env.AZURE_OPENAI_API_KEY!,
  resourceName: 'enclaveidai2163546968',
  // baseURL:
  //   'https://enclaveidai2163546968.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview',
});
