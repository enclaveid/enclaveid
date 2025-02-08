import { streamText } from 'ai';

import { quantitativeAgentConfig } from '../../services/ai/quantitativeAgent/agentConfig';
import { causalInferenceAgentConfig } from '../../services/ai/causalInferenceAgent/agentConfig';
import { nudgingAgentConfig } from '../../services/ai/nudgingAgent/agentConfig';

export type Agent = 'nudging' | 'causal_inference' | 'quantitative_analysis';

export async function POST(req: Request) {
  const { messages, metadata } = await req.json();

  const agentConfig = {
    nudging: nudgingAgentConfig,
    causal_inference: causalInferenceAgentConfig,
    quantitative_analysis: quantitativeAgentConfig,
  }[metadata.agent as Agent];

  const result = streamText({ ...agentConfig, messages });

  // If no markup, return the stream response as normal
  return result.toDataStreamResponse({
    sendReasoning: true,
  });
}
