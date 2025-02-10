import { z } from 'zod';
import { Tool } from 'ai';
import { makeApiRequest } from '../utils';

const sqlQuery: Tool = {
  description:
    'Execute a query on the database using plain SQL (ANSI/ISO standard).',
  parameters: z.object({
    query: z.string(),
    toEmbedNodes: z.array(z.string()).optional(),
    toEmbedRawData: z.array(z.string()).optional(),
  }),
  execute: async ({
    query,
    toEmbedNodes,
    toEmbedRawData,
  }: {
    query: string;
    toEmbedNodes?: string[];
    toEmbedRawData?: string[];
  }) =>
    makeApiRequest('sql_query', {
      query,
      to_embed_nodes: toEmbedNodes ?? [],
      to_embed_raw_data: toEmbedRawData ?? [],
    }),
};

export const quantitativeActions = {
  sqlQuery,
};
