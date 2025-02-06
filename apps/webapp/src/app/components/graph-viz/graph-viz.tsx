import { ChunkTimelineProps, NodeHoverData, NodeData } from './types';
import { useState, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import * as THREE from 'three';
import { SubgraphType } from './types';
import { getSentimentColor } from './helpers';
import { HoverEdges } from './hover-edges';
import { HoverTooltip } from './hover-tooltip';
import { GraphVizCirclePack } from './graph-viz-circle-pack';
import { useCirclePackingLayout } from './useCirclePackingLayout';

export function GraphViz({ chunks, nodes }: ChunkTimelineProps) {
  // 1) Hover (ephemeral) state
  const [hoverData, setHoverData] = useState<NodeHoverData>({
    position: [0, 0],
    node: null,
    visible: false,
  });

  // 2) Selected (sticky) node state
  const [selectedData, setSelectedData] = useState<NodeHoverData | null>(null);

  // Separate out single-chunk nodes vs. multi-chunk (recurrent) nodes
  const [regularNodes, recurrentNodes] = useMemo(() => {
    return [
      nodes.filter((n) => n.chunk_ids.length === 1),
      nodes.filter((n) => n.chunk_ids.length > 1),
    ];
  }, [nodes]);

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
    for (const node of regularNodes) {
      for (const cId of [...new Set(node.chunk_ids)]) {
        if (!map[cId]) {
          map[cId] = [];
        }
        map[cId].push(node);
      }
    }
    return map;
  }, [regularNodes]);

  const [user1, user2] = useMemo(() => {
    return [...new Set(recurrentNodes.map((n) => n.user))].filter(
      (user) => user !== 'both'
    );
  }, [recurrentNodes]);

  const recurrentNodesAreaSide = 350;

  const recurrentCirclePackUser1 = useCirclePackingLayout(
    recurrentNodes.filter((n) => n.user === user1),
    recurrentNodesAreaSide,
    recurrentNodesAreaSide
  );

  const recurrentCirclePackBoth = useCirclePackingLayout(
    recurrentNodes.filter((n) => n.user === 'both'),
    recurrentNodesAreaSide,
    recurrentNodesAreaSide,
    recurrentNodesAreaSide + 50
  );

  const recurrentCirclePackUser2 = useCirclePackingLayout(
    recurrentNodes.filter((n) => n.user === user2),
    recurrentNodesAreaSide,
    recurrentNodesAreaSide,
    (recurrentNodesAreaSide + 50) * 2
  );

  // 1) Store each node's "static" world position (approx) for edges
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

  // Helper to convert a node's world coords to screen coords
  const worldToScreenCoords = (
    object: THREE.Object3D,
    camera: THREE.Camera
  ): [number, number] => {
    const vector = new THREE.Vector3().setFromMatrixPosition(
      object.matrixWorld
    );
    vector.project(camera);
    const x = ((vector.x + 1) * window.innerWidth) / 2;
    const y = ((-vector.y + 1) * window.innerHeight) / 2;
    return [x, y];
  };

  // Handler to set pinned node data upon click
  const handleNodeClick = (e: THREE.Event, node: NodeData) => {
    e.stopPropagation();

    const screenPos = worldToScreenCoords(e.object, e.camera);
    // Also store the actual 3D world position so edges draw from correct point
    const worldPos = e.object.getWorldPosition(new THREE.Vector3());

    setSelectedData({
      position: screenPos,
      node,
      visible: true,
      worldPosition: [worldPos.x, worldPos.y, worldPos.z],
    });
  };

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
        // 3) If user clicks on empty space, clear the selected node
        onPointerMissed={() => {
          setSelectedData(null);
        }}
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
                              // 2a) Set pinned node on click
                              onPointerDown={(e) => handleNodeClick(e, node)}
                              // 1a) Hover state
                              onPointerEnter={(e) => {
                                e.stopPropagation();
                                const [x, y] = worldToScreenCoords(
                                  e.object,
                                  e.camera
                                );
                                const worldPos = e.object.getWorldPosition(
                                  new THREE.Vector3()
                                );
                                setHoverData({
                                  position: [x, y],
                                  node,
                                  visible: true,
                                  worldPosition: [
                                    worldPos.x,
                                    worldPos.y,
                                    worldPos.z,
                                  ],
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

        {/* The recurrent nodes (circle packed) */}
        <GraphVizCirclePack
          circlePackingPositions={recurrentCirclePackUser1}
          setHoverData={setHoverData}
          // Pass our click handler down to GraphVizCirclePack so it can set pinned node
          onNodeClick={handleNodeClick}
          selectedNodeId={selectedData?.node?.id}
        />
        <GraphVizCirclePack
          circlePackingPositions={recurrentCirclePackBoth}
          setHoverData={setHoverData}
          onNodeClick={handleNodeClick}
          selectedNodeId={selectedData?.node?.id}
        />
        <GraphVizCirclePack
          circlePackingPositions={recurrentCirclePackUser2}
          setHoverData={setHoverData}
          onNodeClick={handleNodeClick}
          selectedNodeId={selectedData?.node?.id}
        />

        {/* 4) Two sets of edges: ephemeral hovered node + pinned node */}
        <HoverEdges
          hoveredNode={hoverData.visible ? hoverData.node : null}
          nodePositions={
            hoverData.worldPosition
              ? {
                  ...nodePositions,
                  [hoverData.node?.id || '']: hoverData.worldPosition,
                }
              : nodePositions
          }
          allNodes={nodes}
        />

        <HoverEdges
          hoveredNode={selectedData?.node || null}
          nodePositions={
            selectedData?.worldPosition
              ? {
                  ...nodePositions,
                  [selectedData.node?.id || '']: selectedData.worldPosition,
                }
              : nodePositions
          }
          allNodes={nodes}
        />
      </Canvas>

      {/* 5) Two tooltips: ephemeral + pinned */}
      {hoverData.visible && hoverData.node && (
        <HoverTooltip hoverData={hoverData} />
      )}

      {selectedData && selectedData.node && selectedData.visible && (
        <HoverTooltip hoverData={selectedData} />
      )}
    </div>
  );
}
