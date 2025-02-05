import { useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, QuadraticBezierLine, Text } from '@react-three/drei';
import * as THREE from 'three';
import {
  ChunkTimelineProps,
  SubgraphType,
  NodeHoverData,
  NodeData,
} from './types';
import { getSentimentColor } from './helpers';

export function GraphViz({ chunks, nodes: allNodes }: ChunkTimelineProps) {
  const [hoverData, setHoverData] = useState<NodeHoverData>({
    position: [0, 0],
    node: null,
    visible: false,
  });

  // TODO: split ndoes based on recurrence
  const [nodes, recurrentNodes] = useMemo(() => {
    return [
      allNodes.filter((n) => n.chunk_ids.length === 1),
      allNodes.filter((n) => n.chunk_ids.length > 1),
    ];
  }, [allNodes]);

  // Basic layout constants
  const margin = { top: 20, right: 20, bottom: 40, left: 20 };
  const fixedChunkWidth = 300;
  const minChunkHeight = 50;
  const padding = 20;
  const horizontalGap = 20;
  const lineHeight = 20;
  const subgraphTypes: SubgraphType[] = ['meta', 'context', 'attributes'];
  const subgraphColors: Record<SubgraphType, string> = {
    meta: '#ffaaaa',
    context: '#aaffaa',
    attributes: '#aaaaff',
  };

  // Sort chunks
  const sortedChunks = useMemo(() => {
    return [...chunks].sort((a, b) => Number(a.chunk_id) - Number(b.chunk_id));
  }, [chunks]);

  // Simple x-position per chunk
  const chunkLayout = useMemo(() => {
    return sortedChunks.map((chunk, idx) => {
      const x = margin.left + idx * (fixedChunkWidth + horizontalGap);
      return { ...chunk, x };
    });
  }, [sortedChunks, margin.left]);

  // Compute chunk "heights" from naive text wrapping
  const chunkDimensions = useMemo(() => {
    return chunkLayout.map((chunk) => {
      const lines = chunk.messages_str.split('\n');
      const charsPerLine = Math.floor((fixedChunkWidth - 2) / 6);
      const formattedLines = lines.flatMap((line) => {
        const wrappedLines = [];
        for (let i = 0; i < line.length; i += charsPerLine) {
          const isLastLine = i + charsPerLine >= line.length;
          const lineContent = line.slice(i, i + charsPerLine);
          wrappedLines.push(isLastLine ? lineContent : lineContent + '-');
        }
        return wrappedLines;
      });

      const rectHeight = Math.max(
        minChunkHeight,
        formattedLines.length * lineHeight + padding
      );

      return {
        ...chunk,
        height: rectHeight,
        formattedLines,
      };
    });
  }, [chunkLayout]);

  // Map chunk_id => array of nodes
  const chunkNodeMap = useMemo(() => {
    const map: Record<string, NodeData[]> = {};
    for (const node of nodes) {
      for (const cId of [...new Set(node.chunk_ids)]) {
        if (!map[cId]) {
          map[cId] = [];
        }
        map[cId].push(node);
      }
    }
    return map;
  }, [nodes]);

  // 1) Store each node's world position in a dictionary for use in edges
  const nodePositions = useMemo(() => {
    const positions: Record<string, [number, number, number]> = {};

    chunkDimensions.forEach((c) => {
      const chunkCenterX = c.x + fixedChunkWidth / 2;
      // The center of the rectangle in Y
      const chunkCenterY = -(margin.top + c.height / 2);

      // All nodes for this chunk
      const theseNodes = chunkNodeMap[c.chunk_id.toString()] || [];

      // Place the 3 "columns" above the chunk
      subgraphTypes.forEach((sgType, colIdx) => {
        const colNodes = theseNodes.filter((n) =>
          n.subgraph_types.includes(sgType)
        );
        // Center each column
        const columnWidth = fixedChunkWidth / 3;
        const colX =
          chunkCenterX - fixedChunkWidth / 2 + columnWidth * (colIdx + 0.5);

        // Place the nodes in that column
        colNodes.forEach((node, nodeIdx) => {
          const nodeY = chunkCenterY + c.height / 2 + 40 + nodeIdx * 50;
          positions[node.id] = [colX, nodeY, 0];
        });
      });
    });

    return positions;
  }, [chunkDimensions, chunkNodeMap, subgraphTypes, margin.top]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas
        orthographic
        camera={{
          zoom: 0.5,
          position: [0, 0, 100],
          up: [0, 1, 0],
          near: 0.1,
          far: 10000,
        }}
        style={{ background: '#222', width: '100%', height: '100%' }}
      >
        <OrbitControls
          enableZoom
          enablePan
          enableRotate={false}
          mouseButtons={{
            LEFT: THREE.MOUSE.PAN,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.ROTATE,
          }}
          screenSpacePanning
          zoomToCursor
          target0={new THREE.Vector3(0, 0, 0)}
        />

        {/* Render each chunk */}
        {chunkDimensions.map((c) => {
          const color = getSentimentColor(c.sentiment);
          const planeX = c.x + fixedChunkWidth / 2;
          const planeY = -(margin.top + c.height / 2);

          // The nodes that belong to this chunk
          const theseNodes = chunkNodeMap[c.chunk_id.toString()] || [];

          return (
            <group key={c.chunk_id.toString()} position={[planeX, planeY, 0]}>
              {/* The rectangle for the chunk */}
              <mesh>
                <planeGeometry args={[fixedChunkWidth, c.height]} />
                <meshBasicMaterial color={color} />
              </mesh>

              {/* Wrapped text */}
              {c.formattedLines.map((line, idx) => (
                <Text
                  key={idx}
                  color="black"
                  fontSize={12}
                  anchorX="left"
                  anchorY="top"
                  position={[
                    -fixedChunkWidth / 2 + 4,
                    c.height / 2 - 4 - idx * lineHeight,
                    0.1,
                  ]}
                >
                  {line}
                </Text>
              ))}

              {/* Now place the 3 columns of nodes above */}
              <group position={[0, c.height / 2 + 40, 0]}>
                {subgraphTypes.map((sgType, colIdx) => {
                  const colNodes = theseNodes.filter((n) =>
                    n.subgraph_types.includes(sgType)
                  );
                  const columnWidth = fixedChunkWidth / 3;
                  const colX =
                    -fixedChunkWidth / 2 + columnWidth * (colIdx + 0.5);

                  return (
                    <group key={sgType} position={[colX, 0, 0]}>
                      {colNodes.map((node, nodeIdx) => {
                        const nodeY = nodeIdx * 50;
                        return (
                          <group key={node.id} position={[0, nodeY, 0]}>
                            {/* Draw the node circle */}
                            <mesh
                              onPointerEnter={(e) => {
                                e.stopPropagation();
                                // Convert world coords to screen coords
                                const vector =
                                  new THREE.Vector3().setFromMatrixPosition(
                                    e.object.matrixWorld
                                  );
                                vector.project(e.camera);
                                const x =
                                  ((vector.x + 1) * window.innerWidth) / 2;
                                const y =
                                  ((-vector.y + 1) * window.innerHeight) / 2;

                                setHoverData({
                                  position: [x, y],
                                  node: node,
                                  visible: true,
                                });
                              }}
                              onPointerLeave={() => {
                                setHoverData((prev) => ({
                                  ...prev,
                                  visible: false,
                                }));
                              }}
                            >
                              <circleGeometry args={[18, 32]} />
                              <meshBasicMaterial
                                color={subgraphColors[sgType]}
                              />
                            </mesh>
                          </group>
                        );
                      })}
                    </group>
                  );
                })}
              </group>
            </group>
          );
        })}

        {/* 2) The curved "jump" lines for the hovered node’s inbound/outbound edges */}
        <HoverEdges
          hoveredNode={hoverData.visible ? hoverData.node : null}
          nodePositions={nodePositions}
          allNodes={nodes}
        />
      </Canvas>

      {/* Hover tooltip */}
      {hoverData.visible && hoverData.node && (
        <div
          style={{
            position: 'absolute',
            left: hoverData.position[0],
            top: hoverData.position[1],
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
            <strong>ID:</strong> {hoverData.node.id}
          </div>
          <div>
            <strong>User:</strong> {hoverData.node.user}
          </div>
          <div>
            <strong>Proposition:</strong> {hoverData.node.proposition}
          </div>
          <div>
            <strong>Node type:</strong> {hoverData.node.subgraph_types[0]}
          </div>
          <div>
            <strong>Relationships:</strong>{' '}
            {hoverData.node.relationships.length}
          </div>
        </div>
      )}
    </div>
  );
}

// ----- Component to render the "humped" edges on hover -----
type HoverEdgesProps = {
  hoveredNode: NodeData | null;
  nodePositions: Record<string, [number, number, number]>;
  allNodes: NodeData[];
};

// Renders bright-blue arcs for outgoing edges and bright-red arcs for incoming edges
function HoverEdges({ hoveredNode, nodePositions, allNodes }: HoverEdgesProps) {
  // If no node is hovered, render nothing
  if (!hoveredNode) return null;

  // We want *all* edges that connect to hoveredNode, either as source or target.
  // By default, each node in `allNodes` has an array of relationships = { source, target }
  // Usually that means "source: this node, target: other node," but it may vary.
  // If your data only stores outbound edges in `relationships`, we need to find inbound edges by checking all others.
  const edges = [];

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
            mid={mid}
            color={edge.color}
            lineWidth={3}
            dashed={false}
          />
        );
      })}
    </>
  );
}
