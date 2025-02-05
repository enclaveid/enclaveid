import { useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import * as THREE from 'three';
import { ChunkTimelineProps, SubgraphType, NodeHoverData } from './types';
import { getSentimentColor } from './helpers';

export function GraphViz({ chunks, nodes }: ChunkTimelineProps) {
  // Add state for hover data
  const [hoverData, setHoverData] = useState<NodeHoverData>({
    position: [0, 0],
    node: null,
    visible: false,
  });

  // Layout parameters
  const margin = { top: 20, right: 20, bottom: 40, left: 20 };
  const fixedChunkWidth = 300;
  const minChunkHeight = 50;
  const padding = 20;
  const horizontalGap = 20;
  const lineHeight = 20;

  // We'll keep an easy reference for subgraph layout:
  const subgraphTypes: SubgraphType[] = ['meta', 'context', 'attributes'];
  const subgraphColors: Record<SubgraphType, string> = {
    meta: '#ffaaaa', // pink-ish
    context: '#aaffaa', // green-ish
    attributes: '#aaaaff', // blue-ish
  };

  // Sort the chunks in ascending order
  const sortedChunks = useMemo(() => {
    return [...chunks].sort((a, b) => Number(a.chunk_id) - Number(b.chunk_id));
  }, [chunks]);

  // Simple left-to-right "index-based" layout for chunks
  const chunkLayout = useMemo(() => {
    return sortedChunks.map((chunk, idx) => {
      const x = margin.left + idx * (fixedChunkWidth + horizontalGap);
      return { ...chunk, x };
    });
  }, [sortedChunks, margin.left]);

  // Compute chunk "heights" based on text wrapping (just as in your original code)
  const chunkDimensions = useMemo(() => {
    return chunkLayout.map((chunk) => {
      // Rough text wrapping logic
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

  // For easy lookups: map chunk_id -> array of node objects
  const chunkNodeMap = useMemo(() => {
    const map: Record<string, Array<(typeof nodes)[0]>> = {};
    for (const node of nodes) {
      for (const cId of node.chunk_ids) {
        if (!map[cId]) {
          map[cId] = [];
        }
        map[cId].push(node);
      }
    }
    return map;
  }, [nodes]);

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
          enableDamping={false}
          mouseButtons={{
            LEFT: THREE.MOUSE.PAN,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.ROTATE,
          }}
          screenSpacePanning
          zoomToCursor
          target0={new THREE.Vector3(0, 0, 0)}
        />

        {/* Render each chunk as a rectangle + text, then the node columns above it */}
        {chunkDimensions.map((c) => {
          const color = getSentimentColor(c.sentiment);
          const planeX = c.x + fixedChunkWidth / 2;
          const planeY = -(margin.top + c.height / 2);

          // The nodes that belong to this chunk, if any
          const theseNodes = chunkNodeMap[c.chunk_id.toString()] || [];

          return (
            <group key={c.chunk_id.toString()} position={[planeX, planeY, 0]}>
              {/* The rectangle plane for the chunk */}
              <mesh>
                <planeGeometry args={[fixedChunkWidth, c.height]} />
                <meshBasicMaterial color={color} />
              </mesh>

              {/* Wrapped text inside the chunk */}
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

              {/* Now place the 3 "columns" of nodes above the rectangle */}
              <group position={[0, c.height / 2 + 40, 0]}>
                {subgraphTypes.map((sgType, colIdx) => {
                  // Filter to nodes whose subgraph_types includes this sgType
                  const colNodes = theseNodes.filter((n) =>
                    n.subgraph_types.includes(sgType)
                  );

                  // We'll divide the fixedChunkWidth into 3 equal columns
                  const columnWidth = fixedChunkWidth / 3;
                  // Center each column
                  const colX =
                    -fixedChunkWidth / 2 + columnWidth * (colIdx + 0.5);

                  return (
                    <group key={sgType} position={[colX, 0, 0]}>
                      {colNodes.map((node, nodeIdx) => {
                        const nodeY = nodeIdx * 50;
                        return (
                          <group key={node.id} position={[0, nodeY, 0]}>
                            <mesh
                              onPointerEnter={(e) => {
                                e.stopPropagation();
                                // Convert 3D position to screen coordinates
                                const vector = new THREE.Vector3();
                                vector.setFromMatrixPosition(
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
          {/* <div>
            <strong>Datetimes:</strong> {hoverData.node.datetimes.join(', ')}
          </div>
          <div>
            <strong>Types:</strong> {hoverData.node.subgraph_types.join(', ')}
          </div>
          */}
          {/* <div>
            <strong>Chunk IDs:</strong> {hoverData.node.chunk_ids.join(', ')}
          </div> */}
          <div>
            <strong>Relationships:</strong>{' '}
            {hoverData.node.relationships.length}
          </div>
        </div>
      )}
    </div>
  );
}
