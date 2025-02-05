import { NodeData } from './types';

import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { GraphVizCirclePackProps } from './types';
import { useMemo } from 'react';
import { pack, hierarchy } from 'd3-hierarchy';

function computeCirclePackingLayout(
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

export function GraphVizCirclePack({
  nodes,
  hoverData,
  setHoverData,
}: GraphVizCirclePackProps) {
  // 1) compute layout once
  const width = 600; // or however large you want your circle packing region
  const height = 600;
  const circlePositions = useMemo(() => {
    if (nodes.length === 0) return [];
    return computeCirclePackingLayout(nodes, width, height);
  }, [nodes, width, height]);

  return (
    <Canvas
      orthographic
      camera={{
        zoom: 1,
        position: [0, 0, 100],
        up: [0, 1, 0],
      }}
      style={{ background: '#333', width: '100%', height: '100%' }}
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
      />

      {/* Render each packed node as a circle */}
      {circlePositions.map(({ x, y, r, node }) => {
        return (
          <group key={node.id} position={[x - width / 2, -y + height / 2, 0]}>
            <mesh
              onPointerEnter={(e) => {
                e.stopPropagation();
                const vector = new THREE.Vector3().setFromMatrixPosition(
                  e.object.matrixWorld
                );
                vector.project(e.camera);
                const sx = ((vector.x + 1) * window.innerWidth) / 2;
                const sy = ((-vector.y + 1) * window.innerHeight) / 2;

                setHoverData({
                  position: [sx, sy],
                  node,
                  visible: true,
                });
              }}
              onPointerLeave={() => {
                setHoverData((prev) => ({ ...prev, visible: false }));
              }}
            >
              <circleGeometry args={[r, 32]} />
              <meshBasicMaterial color="#ffcc00" />
            </mesh>
          </group>
        );
      })}

      {/* If you want to show edges among recurrent nodes, you can do so similarly,
          or re-use a <HoverEdges> approach with a specialized nodePositions, etc. */}
    </Canvas>
  );
}
