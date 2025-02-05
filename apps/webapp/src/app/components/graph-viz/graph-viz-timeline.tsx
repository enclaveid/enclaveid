import { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import * as THREE from 'three';
import { SubgraphType, NodeHoverData, NodeData, ChunkData } from './types';
import { getSentimentColor } from './helpers';
import { HoverEdges } from './hover-edges';

export function GraphVizTimeline({
  chunks,
  nodes,
  hoverData,
  setHoverData,
}: {
  chunks: ChunkData[];
  nodes: NodeData[];
  hoverData: NodeHoverData;
  setHoverData: React.Dispatch<React.SetStateAction<NodeHoverData>>;
}) {
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
    </div>
  );
}
