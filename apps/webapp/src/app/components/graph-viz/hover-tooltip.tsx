import { NodeHoverData } from './types';

export function HoverTooltip({ hoverData }: { hoverData: NodeHoverData }) {
  if (!hoverData.visible || !hoverData.node) return null;

  const {
    position: [x, y],
    node,
  } = hoverData;

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '8px',
        borderRadius: '4px',
        fontSize: '12px',
        pointerEvents: 'none',
        transform: 'translate(-50%, -100%)',
        marginTop: '-10px',
        maxWidth: '300px',
        zIndex: 1000,
      }}
    >
      <div>
        <strong>ID:</strong> {node.id}
      </div>
      <div>
        <strong>User:</strong> {node.user}
      </div>
      <div>
        <strong>Proposition:</strong> {node.proposition}
      </div>
      <div>
        <strong>Node type:</strong> {node.subgraph_types[0]}
      </div>
      <div>
        <strong>Relationships:</strong> {node.relationships.length}
      </div>
    </div>
  );
}
