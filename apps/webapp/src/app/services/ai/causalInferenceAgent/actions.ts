import { z } from 'zod';

// Helper function for making API requests
async function makeApiRequest(endpoint: string, data: Record<string, any>) {
  const response = await fetch(`http://127.0.0.1:8000/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) throw new Error(`Failed to fetch ${endpoint}`);
  return response.json();
}

const getSimilarNodes = {
  description:
    'Get nodes similar to the query. This action is useful to gather evidence and counterevidence for the hypothesis.',
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }: { query: string }) =>
    makeApiRequest('similar_nodes', { query }),
};

const getCausalChain = {
  description:
    'Get the causal chain between two nodes. If no direct causal chain is found, it will return the closest one.',
  parameters: z.object({
    node1: z.string(),
    node2: z.string(),
  }),
  execute: async ({ node1, node2 }: { node1: string; node2: string }) =>
    makeApiRequest('causal_chain', { node_id1: node1, node_id2: node2 }),
};

const getEffects = {
  description:
    'Explore the immediate (if depth=1) or indirect (if depth>1) effects of the current node, with their metadata properties.',
  parameters: z.object({
    node: z.string(),
    depth: z.number().optional(),
  }),
  execute: async ({ node, depth = 1 }: { node: string; depth?: number }) =>
    makeApiRequest('children', { node_id: node, depth }),
};

const getCauses = {
  description:
    'Explore the immediate causes of the current node, with their metadata properties.',
  parameters: z.object({
    node: z.string(),
  }),
  execute: async ({ node }: { node: string }) =>
    makeApiRequest('parents', { node_id: node }),
};

const getRawData = {
  description:
    'Get the raw data underlying the propostion of the given node. Use this action to assess the strenght of the proposition.',
  parameters: z.object({
    node: z.string(),
  }),
  execute: async ({ node }: { node: string }) =>
    makeApiRequest('raw_data', { node_id: node }),
};

export const step1Actions = {
  getSimilarNodes,
};

export const step2Actions = {
  getCausalChain,
  getEffects,
  getCauses,
  getRawData,
};

export function serializeActions(actions: Record<string, any>): string {
  return Object.entries(actions)
    .map(([name, action]) => {
      const params = Object.keys(action.parameters.shape);
      const functionSignature = `${name}(${params.join(', ')})`;
      return `- ${functionSignature}: ${action.description}`;
    })
    .join('\n');
}

export async function parseAndExecuteActions(rawActionsJson: string) {
  // Extract JSON object using regex
  const jsonMatch = rawActionsJson.match(/\{[\s\S]*\}/);

  if (!jsonMatch) return null;

  const actionsArray = JSON.parse(jsonMatch[0]).actions;

  const actions = {
    ...step1Actions,
    ...step2Actions,
  };

  const results = await Promise.all(
    actionsArray.map(
      async (action: { name: string; args: Record<string, any> }) => {
        const { name, args } = action;
        const actionFunction = actions[name as keyof typeof actions];

        if (!actionFunction) {
          throw new Error(`Unknown action: ${name}`);
        }

        const result = await actionFunction.execute(args as any);
        return { name, args, result };
      }
    )
  );

  // Transform array of results into a record
  const resultsRecord = results.reduce(
    (acc, { name, args, result }) => ({
      ...acc,
      [name]: { args, result },
    }),
    {} as Record<string, { args: Record<string, any>; result: any }>
  );

  return JSON.stringify(resultsRecord, null, 2);
}
