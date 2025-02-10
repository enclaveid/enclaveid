import { tool, streamText, DataStreamWriter } from 'ai';
import { nudgingAgentSystemPrompt } from './systemPrompt';
import { anthropic } from '@ai-sdk/anthropic';
import { z } from 'zod';
import { runAgentUntilComplete } from '../runAgentUntilComplete';
import { causalInferenceAgentConfig } from '../causalInferenceAgent/agentConfig';
import { quantitativeAgentConfig } from '../quantitativeAgent/agentConfig';

export const nudgingAgentConfig = (
  streamWriter: DataStreamWriter
): Parameters<typeof streamText>[0] => {
  return {
    model: anthropic('claude-3-5-sonnet-20241022'),
    system: nudgingAgentSystemPrompt,
    maxTokens: 8192,
    tools: {
      causalInference: tool({
        description: `
        Causal inference on a causal graph covering all that can be confidently inferred about the relationship's context.
          With this tool you can validate hypotheses such as:
"The root misunderstanding stems from a cycle of insecure attachment styles where USER1's fear of commitment and emotional volatility triggers USER2's anxious attachment, leading to a destructive pattern of paradoxical threats and mistrust. Both partners project their insecurities through conflicting communication strategies, exacerbating mutual fears of abandonment and insufficient emotional support."
          `,
        parameters: z.object({
          query: z.string(),
        }),
        execute: async ({ query }, { toolCallId }) => {
          return await runAgentUntilComplete(
            toolCallId,
            query,
            streamWriter,
            causalInferenceAgentConfig
          );
        },
      }),
      quantitativeAnalysis: tool({
        description: `
        A quantitative analysis tool to access the raw data underlying the causal graph.
        With this tool you can answer questions such as:
        "How many times did USER1 and USER2 text each other in the last 30 days?"
        `,
        parameters: z.object({
          query: z.string(),
        }),
        execute: async ({ query }, { toolCallId }) => {
          return await runAgentUntilComplete(
            toolCallId,
            query,
            streamWriter,
            quantitativeAgentConfig
          );
        },
      }),
      suggestNextQuestions: tool({
        description: `
        Suggest the user more questions to explore the previous response vertically or horizontally.
        `,
        parameters: z.object({
          horizontal: z.array(z.string()),
          vertical: z.array(z.string()),
        }),
      }),
    },
  };
};
