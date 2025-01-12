export const NodeType = {
  Observable: 'Observable',
  Inferrable: 'Inferrable',
  Speculative: 'Speculative',
} as const;
export type NodeType = (typeof NodeType)[keyof typeof NodeType];
