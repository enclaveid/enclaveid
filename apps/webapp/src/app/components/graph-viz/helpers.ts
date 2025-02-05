import { NodeData } from './types';
import { hierarchy, pack } from 'd3-hierarchy';

export function getSentimentColor(sentiment: number): string {
  // Ensure sentiment is between -1 and 1
  const normalizedSentiment = Math.max(-1, Math.min(1, sentiment));

  // Convert to a 0-1 scale for interpolation
  const t = (normalizedSentiment + 1) / 2;

  const red = Math.round(255 - 175 * t);
  const green = Math.round(80 + 175 * t);
  const blue = 0;

  return `rgb(${red}, ${green}, ${blue})`;
}

export function computeCirclePackingLayout(
  nodes: NodeData[],
  width: number,
  height: number
) {
  // Step 1: Create hierarchy with frequency scaling for sizes
  const root = hierarchy({ children: nodes }).sum((d) => {
    const node = d as unknown as NodeData;
    return Number(node.frequency);
  });

  // Step 2: Use d3 pack layout
  const packLayout = pack<typeof root.data>().size([width, height]).padding(5);

  const packedRoot = packLayout(root);

  // Step 3: Extract positions
  const circles: { x: number; y: number; r: number; node: NodeData }[] = [];

  // all nodes will be in `packedRoot.leaves()`
  for (const leaf of packedRoot.leaves()) {
    const { x, y, r } = leaf;
    const node = leaf.data as unknown as NodeData;
    circles.push({ x, y, r, node });
  }

  return circles;
}
