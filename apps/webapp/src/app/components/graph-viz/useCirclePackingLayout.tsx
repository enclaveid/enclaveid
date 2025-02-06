import { computeCirclePackingLayout } from './helpers';
import { useMemo } from 'react';
import { NodeData } from './types';

export function useCirclePackingLayout(
  nodes: NodeData[],
  width: number,
  height: number,
  xOffset = 0,
  yOffset = 0
) {
  return useMemo(() => {
    if (nodes.length === 0) return [];
    return computeCirclePackingLayout(nodes, width, height, xOffset, yOffset);
  }, [nodes, width, height, xOffset, yOffset]);
}
