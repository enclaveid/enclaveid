import { z } from 'zod';
import { Tool } from 'ai';
import { makeApiRequest } from '../utils';

const sqlQuery: Tool = {
  description:
    'Execute a query on the database using plain SQL (ANSI/ISO standard).',
  parameters: z.object({
    query: z.string(),
  }),
  execute: async ({ query }: { query: string }) =>
    makeApiRequest('sql_query', { query }),
};

export const quantitativeActions = {
  sqlQuery,
};
