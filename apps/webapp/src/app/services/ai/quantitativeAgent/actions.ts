import { z } from 'zod';
import { Tool, tool } from 'ai';
import { makeApiRequest } from '../utils';

const sqlQuery: Tool = tool({
  description: `
  Execute a query on the database using SQL.
  Use the "toEmbedNodes" and "toEmbedRawData" fields if you want to compare text to nodes or raw data embeddings, respectively.
  For example, if you want to find the top 5 raw data chunks that are most similar to the text "I love you", call the tool with:
  {
    "query": "SELECT * FROM RawDataChunk ORDER BY embedding <=> (SELECT embedding FROM QueryEmbedding WHERE id = 0 and type = 'raw_data') LIMIT 5",
    "toEmbedRawData": ["I love you"] // Note how we select the QueryEmbedding with id = 0 (the array index) and type = 'raw_data'
    "toEmbedNodes": [],
  }

  `,
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
});

export const quantitativeActions = {
  sqlQuery,
};
