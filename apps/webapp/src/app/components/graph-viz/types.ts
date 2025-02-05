// Types (same as in your example)
export type ChunkData = {
  chunk_id: bigint;
  sentiment: number;
  start_dt: string;
  end_dt: string;
  messages_str: string;
};

export type SubgraphType = 'meta' | 'context' | 'attributes';

export type NodeData = {
  id: string;
  user: string;
  proposition: string;
  datetimes: string[];
  subgraph_types: SubgraphType[];
  chunk_ids: string[];
  relationships: Array<{ source: string; target: string }>;
};

export type ChunkTimelineProps = {
  chunks: ChunkData[];
  nodes: NodeData[];
};
