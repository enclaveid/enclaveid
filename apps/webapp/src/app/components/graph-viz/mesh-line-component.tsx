// 1. Import and extend meshline
import { extend } from '@react-three/fiber';
import { MeshLineGeometry, MeshLineMaterial } from 'meshline';

declare module '@react-three/fiber' {
  interface ThreeElements {
    meshLineGeometry: any;
    meshLineMaterial: any;
  }
}

extend({ MeshLineGeometry, MeshLineMaterial });

export function MeshLineComponent({
  points,
  color,
  lineWidth,
  isHighlighted,
}: {
  points: [number, number, number][]; // 3D coords
  color: string;
  lineWidth: number;
  isHighlighted: boolean;
}) {
  return (
    <mesh>
      {/* The geometry that forms the line tube */}
      <meshLineGeometry attach="geometry" points={points} />
      {/* The material with thickness & color */}
      <meshLineMaterial
        attach="material"
        color={color}
        lineWidth={lineWidth}
        transparent
        opacity={isHighlighted ? 1 : 0.8}
        depthTest={false} // allow line to be drawn "on top" if you like
        resolution={[window.innerWidth, window.innerHeight]}
        // ^ This is important so meshline knows how to handle line thickness
      />
    </mesh>
  );
}
