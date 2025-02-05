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
  frequency: bigint;
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

export type NodeHoverData = {
  position: [number, number];
  node: NodeData | null;
  visible: boolean;
};

export type HoverEdgesProps = {
  hoveredNode: NodeData | null;
  nodePositions: Record<string, [number, number, number]>;
  allNodes: NodeData[];
};

export type GraphVizCirclePackProps = {
  nodes: NodeData[];
  hoverData: NodeHoverData;
  setHoverData: React.Dispatch<React.SetStateAction<NodeHoverData>>;
};
