export const NodeType = {
  observable: 'observable',
  inferrable: 'inferrable',
  speculative: 'speculative',
} as const;
export type NodeType = (typeof NodeType)[keyof typeof NodeType];
