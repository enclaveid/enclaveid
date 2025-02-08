import { z } from 'zod';
import { Tool, ToolSet } from 'ai';
import { makeApiRequest } from '../utils';

const getSimilarNodes: Tool = {
  description:
    'Get nodes similar to the query. This action is useful to gather evidence and counterevidence for the hypothesis.',
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }: { query: string }) =>
    makeApiRequest('similar_nodes', { query }),
};

const getCausalChain: Tool = {
  description:
    'Get the causal chain between two nodes. If no direct causal chain is found, it will return the closest one.',
  parameters: z.object({
    node1: z.string(),
    node2: z.string(),
  }),
  execute: async ({ node1, node2 }: { node1: string; node2: string }) =>
    makeApiRequest('causal_chain', { node_id1: node1, node_id2: node2 }),
};

const getEffects: Tool = {
  description:
    'Explore the immediate (if depth=1) or indirect (if depth>1) effects of the current node, with their metadata properties.',
  parameters: z.object({
    node: z.string(),
    depth: z.number().optional(),
  }),
  execute: async ({ node, depth = 1 }: { node: string; depth?: number }) =>
    makeApiRequest('children', { node_id: node, depth }),
};

const getCauses: Tool = {
  description:
    'Explore the immediate causes of the current node, with their metadata properties.',
  parameters: z.object({
    node: z.string(),
  }),
  execute: async ({ node }: { node: string }) =>
    makeApiRequest('parents', { node_id: node }),
};

const getRawData: Tool = {
  description:
    'Get the raw data underlying the propostion of the given node. Use this action to assess the strenght of the proposition.',
  parameters: z.object({
    node: z.string(),
  }),
  execute: async ({ node }: { node: string }) =>
    makeApiRequest('raw_data', { node_id: node }),
};

export const causalInferenceActions: ToolSet = {
  getSimilarNodes,
  getCausalChain,
  getEffects,
  getCauses,
  getRawData,
};
