import { useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { NodeData, NodeHoverData } from './types';

export function GraphVizCirclePack({
  circlePackingPositions,
  setHoverData,
}: {
  circlePackingPositions: { x: number; y: number; r: number; node: NodeData }[];
  setHoverData: (hoverData: NodeHoverData) => void;
}) {
  const circlePackRef = useRef<THREE.Group>(null);
  const { camera } = useThree();

  useFrame(() => {
    if (!circlePackRef.current) return;

    // The NDC position for the top-left corner:
    const ndc = new THREE.Vector3(-1, 1, 0);
    // Unproject to transform from NDC -> world space
    ndc.unproject(camera);

    // Move our group to that top-left world position
    circlePackRef.current.position.copy(ndc);

    // If it should NOT scale when zooming in/out:
    // scale inversely to the camera's zoom
    const orthoCam = camera as THREE.OrthographicCamera;
    const invZoom = 1 / orthoCam.zoom;
    circlePackRef.current.scale.set(invZoom, invZoom, invZoom);
  });

  return (
    <>
      <group ref={circlePackRef}>
        {circlePackingPositions.map(({ x, y, r, node }) => {
          return (
            <group key={node.id} position={[x, -y, 0]}>
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
      </group>
    </>
  );
}
