import { QuadraticBezierLine } from '@react-three/drei';
import { HoverEdgesProps } from './types';

// Renders bright-blue arcs for outgoing edges and bright-red arcs for incoming edges
export function HoverEdges({
  hoveredNode,
  nodePositions,
  allNodes,
}: HoverEdgesProps) {
  console.log('hoveredNode', hoveredNode);
  // If no node is hovered, render nothing
  if (!hoveredNode) return null;

  // We want *all* edges that connect to hoveredNode, either as source or target.
  // By default, each node in `allNodes` has an array of relationships = { source, target }
  // Usually that means "source: this node, target: other node," but it may vary.
  // If your data only stores outbound edges in `relationships`, we need to find inbound edges by checking all others.
  const edges: { source: string; target: string; color: string }[] = [];

  // 1) Outgoing edges from hoveredNode itself
  hoveredNode.relationships.forEach((rel) => {
    // If hoveredNode is the source in that relationship
    if (rel.source === hoveredNode.id) {
      edges.push({
        source: rel.source,
        target: rel.target,
        color: 'blue', // outgoing
      });
    }
    // If hoveredNode is the target, treat as incoming
    if (rel.target === hoveredNode.id) {
      edges.push({
        source: rel.source,
        target: rel.target,
        color: 'red',
      });
    }
  });

  // 2) In case *other* nodes store a relationship pointing to hoveredNode,
  //    we find them as well. (Optional, depending on your data shape)
  allNodes.forEach((n) => {
    // skip the hovered node itself (already handled)
    if (n.id === hoveredNode.id) return;
    n.relationships.forEach((rel) => {
      // If hoveredNode is the source
      if (rel.source === hoveredNode.id && rel.target === n.id) {
        edges.push({ source: rel.source, target: rel.target, color: 'blue' });
      }
      // If hoveredNode is the target
      if (rel.target === hoveredNode.id && rel.source === n.id) {
        edges.push({ source: rel.source, target: rel.target, color: 'red' });
      }
    });
  });

  // Remove duplicates if needed (sometimes you might find same edge from both sides).
  // A simple approach: we can use a Set keyed by `${source}->${target}->${color}`
  const unique = new Set<string>();
  const uniqueEdges = edges.filter((e) => {
    const key = `${e.source}:${e.target}:${e.color}`;
    if (unique.has(key)) return false;
    unique.add(key);
    return true;
  });

  // Render a QuadraticBezierLine for each edge
  return (
    <>
      {uniqueEdges.map((edge, i) => {
        const startPos = nodePositions[edge.source];
        const endPos = nodePositions[edge.target];
        if (!startPos || !endPos) return null;

        // Raise midpoint in Y to form a "hump"
        const midX = (startPos[0] + endPos[0]) / 2;
        // Pick a midpoint above the highest node by some offset
        const midY = Math.max(startPos[1], endPos[1]) + 60;
        const mid = [midX, midY, 0];

        return (
          <QuadraticBezierLine
            key={i}
            start={startPos}
            end={endPos}
            mid={mid as [number, number, number]}
            color={edge.color}
            lineWidth={3}
            dashed={false}
          />
        );
      })}
    </>
  );
}
