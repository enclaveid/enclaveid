import { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import * as THREE from 'three';
import { ChunkTimelineProps } from './types';
import { getSentimentColor } from './helpers';

export function GraphViz({ chunks }: ChunkTimelineProps) {
  // Layout parameters
  const margin = { top: 20, right: 20, bottom: 40, left: 20 };
  const fixedChunkWidth = 300;
  const minChunkHeight = 50;
  const padding = 20;
  const horizontalGap = 20;
  const lineHeight = 20;

  // Sort by chunk_id
  const sortedChunks = useMemo(() => {
    return [...chunks].sort((a, b) => Number(a.chunk_id) - Number(b.chunk_id));
  }, [chunks]);

  // Simple left-to-right "index-based" layout
  const chunkLayout = useMemo(() => {
    return sortedChunks.map((chunk, idx) => {
      const x = margin.left + idx * (fixedChunkWidth + horizontalGap);
      return { ...chunk, x };
    });
  }, [sortedChunks, margin.left]);

  // Compute chunk heights with proper text wrapping calculation
  const chunkDimensions = useMemo(() => {
    return chunkLayout.map((chunk) => {
      // Pre-format text into fixed-width lines
      const lines = chunk.messages_str.split('\n');
      const charsPerLine = Math.floor((fixedChunkWidth - 2) / 6); // Rough estimate of chars that fit per line

      // Format each input line into wrapped lines
      const formattedLines = lines.flatMap((line) => {
        const wrappedLines = [];
        for (let i = 0; i < line.length; i += charsPerLine) {
          const isLastLine = i + charsPerLine >= line.length;
          const lineContent = line.slice(i, i + charsPerLine);
          // Add hyphen only if this isn't the last line of the text chunk
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
        formattedLines, // Store pre-formatted lines
      };
    });
  }, [chunkLayout]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Canvas
        // Orthographic camera so that our 2D-like layout doesn't get perspective distortion.
        orthographic
        // Set up a rough initial view:
        camera={{
          zoom: 0.5,
          position: [0, 0, 100], // Position the camera 'above' looking down the Z axis
          up: [0, 1, 0],
          near: 0.1,
          far: 10000,
        }}
        style={{ background: '#222', width: '100%', height: '100%' }}
      >
        {/* OrbitControls provides mouse-driven pan/zoom/rotate. */}
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
          screenSpacePanning={true}
          zoomToCursor={true}
          target0={new THREE.Vector3(0, 0, 0)}
        />

        {/* Chunks rendered as colored planes. We'll place them on the XY plane at z=0. */}
        {chunkDimensions.map((c) => {
          const color = getSentimentColor(c.sentiment);

          // Center the plane so that (x, y) is top-left:
          // By default, a Plane is centered at [0, 0], so we shift by half the width & height.
          const planeX = c.x + fixedChunkWidth / 2;
          const planeY = -(margin.top + c.height / 2); // negative Y so it goes "down" in the canvas

          return (
            <group key={c.chunk_id} position={[planeX, planeY, 0]}>
              {/* The rectangle plane */}
              <mesh>
                <planeGeometry args={[fixedChunkWidth, c.height]} />
                <meshBasicMaterial color={color} />
              </mesh>

              {/* Text (wrapped). We can't directly "wrap" in <Text> but we can do line breaks. */}
              {/* We'll split on newlines and render each line. */}
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
            </group>
          );
        })}
      </Canvas>
    </div>
  );
}
