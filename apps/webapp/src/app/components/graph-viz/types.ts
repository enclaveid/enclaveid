// Types (same as in your example)
export type ChunkData = {
  chunk_id: bigint;
  sentiment: number;
  start_dt: string;
  end_dt: string;
  messages_str: string;
};

export type ChunkTimelineProps = {
  width: number; // For controlling the initial camera, etc.
  height: number; // For controlling the initial camera, etc.
  chunks: ChunkData[];
};
