import { GraphVizCirclePack } from './graph-viz-circle-pack';
import { GraphVizTimeline } from './graph-viz-timeline';
import { HoverTooltip } from './hover-tooltip';
import { ChunkTimelineProps, NodeHoverData } from './types';
import { useState, useMemo } from 'react';

export function GraphViz({ chunks, nodes }: ChunkTimelineProps) {
  const [hoverData, setHoverData] = useState<NodeHoverData>({
    position: [0, 0],
    node: null,
    visible: false,
  });

  // Separate out single-chunk nodes vs. multi-chunk (recurrent) nodes
  const [regularNodes, recurrentNodes] = useMemo(() => {
    return [
      nodes.filter((n) => n.chunk_ids.length === 1),
      nodes.filter((n) => n.chunk_ids.length > 1),
    ];
  }, [nodes]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Main subgraph (chunks + single-chunk nodes) */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '50%',
          height: '100%',
        }}
      >
        <GraphVizTimeline
          chunks={chunks}
          nodes={regularNodes}
          hoverData={hoverData}
          setHoverData={setHoverData}
        />
      </div>

      {/* Separate subgraph (only recurrent nodes) */}
      <div
        style={{
          position: 'absolute',
          right: 0,
          top: 0,
          width: '50%',
          height: '100%',
        }}
      >
        <GraphVizCirclePack
          nodes={recurrentNodes}
          hoverData={hoverData}
          setHoverData={setHoverData}
        />
      </div>

      {/* Hover tooltip can be placed at the parent level, so it appears over both canvases */}
      {hoverData.visible && hoverData.node && (
        <HoverTooltip hoverData={hoverData} />
      )}
    </div>
  );
}
