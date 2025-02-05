import { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text } from '@react-three/drei';
import { scaleTime } from 'd3-scale';
import { timeParse, timeFormat } from 'd3-time-format';
import * as THREE from 'three';

// Types (same as in your example)
export type ChunkData = {
  chunk_id: string;
  sentiment: string;
  start_dt: string;
  end_dt: string;
  messages_str: string;
};

const parseDate = timeParse('%Y-%m-%dT%H:%M:%S');
const formatDate = timeFormat('%b %d, %Y %H:%M');

type ChunkTimelineProps = {
  width: number; // For controlling the initial camera, etc.
  height: number; // For controlling the initial camera, etc.
  chunks: ChunkData[];
};

// Helper function to interpolate between vibrant red and green
function getSentimentColor(sentiment: number): string {
  // Ensure sentiment is between -1 and 1
  const normalizedSentiment = Math.max(-1, Math.min(1, sentiment));

  // Convert to a 0-1 scale for interpolation
  const t = (normalizedSentiment + 1) / 2;

  const red = Math.round(255 - 175 * t);
  const green = Math.round(80 + 175 * t);
  const blue = 0;

  return `rgb(${red}, ${green}, ${blue})`;
}

export function GraphViz({
  width = 1000,
  height = 400,
  chunks,
}: ChunkTimelineProps) {
  // Layout parameters
  const margin = { top: 20, right: 20, bottom: 40, left: 20 };
  const fixedChunkWidth = 300;
  const minChunkHeight = 50;
  const padding = 20;
  const horizontalGap = 20;
  const lineHeight = 20;

  // Convert chunk start/end to Date
  const chunksParsed = useMemo(() => {
    return chunks.map((c) => {
      const start = parseDate(c.start_dt) ?? new Date(c.start_dt);
      const end = parseDate(c.end_dt) ?? new Date(c.end_dt);
      return { ...c, start, end };
    });
  }, [chunks]);

  const minTime = useMemo(
    () => new Date(Math.min(...chunksParsed.map((c) => c.start.getTime()))),
    [chunksParsed]
  );
  const maxTime = useMemo(
    () => new Date(Math.max(...chunksParsed.map((c) => c.end.getTime()))),
    [chunksParsed]
  );

  // Scale for time -> x positions (for axis)
  const xScale = useMemo(() => {
    return scaleTime<number>({
      domain: [minTime, maxTime],
      range: [margin.left, width - margin.right],
    });
  }, [minTime, maxTime, width, margin]);

  // Sort by start time
  const sortedChunks = useMemo(() => {
    return [...chunksParsed].sort(
      (a, b) => a.start.getTime() - b.start.getTime()
    );
  }, [chunksParsed]);

  // Simple left-to-right "index-based" layout
  const chunkLayout = useMemo(() => {
    return sortedChunks.map((chunk, idx) => {
      const x = margin.left + idx * (fixedChunkWidth + horizontalGap);
      return { ...chunk, x };
    });
  }, [sortedChunks]);

  // Adjust total width to accommodate all chunk rectangles
  const totalWidth = useMemo(() => {
    return Math.max(
      width,
      margin.left +
        chunkLayout.length * (fixedChunkWidth + horizontalGap) -
        horizontalGap +
        margin.right
    );
  }, [chunkLayout, width, margin]);

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

  // For the sake of demonstration, we'll stack them in a single row,
  // so total height is margin + chunkHeight + margin
  const totalHeight = useMemo(() => {
    const maxH = Math.max(...chunkDimensions.map((c) => c.height), height);
    return margin.top + maxH + margin.bottom;
  }, [chunkDimensions, height, margin]);

  // -- Axis Ticks in 3D -----------------------------------
  // We'll create a small component to render an axis line + ticks (at y=0 for example).
  const AxisBottom3D = ({
    xScale,
    yPosition = 0,
    zPosition = 0,
    tickCount = 5,
  }: {
    xScale: (val: Date) => number;
    yPosition?: number;
    zPosition?: number;
    tickCount?: number;
  }) => {
    const ticks = xScale.ticks(tickCount);

    return (
      <group>
        {/* Axis line (from minTime to maxTime) */}
        <lineSegments>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              array={
                new Float32Array([
                  xScale(minTime),
                  yPosition,
                  zPosition,
                  xScale(maxTime),
                  yPosition,
                  zPosition,
                ])
              }
              count={2}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="white" />
        </lineSegments>

        {/* Ticks */}
        {ticks.map((t, i) => {
          const tickX = xScale(t);
          return (
            <group key={i} position={[tickX, yPosition, zPosition]}>
              {/* Tick line */}
              <lineSegments>
                <bufferGeometry>
                  <bufferAttribute
                    attach="attributes-position"
                    array={
                      new Float32Array([
                        0,
                        0,
                        0, // start
                        0,
                        -5,
                        0, // end (5px down in "screen" units)
                      ])
                    }
                    count={2}
                    itemSize={3}
                  />
                </bufferGeometry>
                <lineBasicMaterial color="white" />
              </lineSegments>
              {/* Tick label */}
              <Text
                color="white"
                fontSize={8}
                position={[0, -15, 0]}
                anchorX="center"
                anchorY="middle"
              >
                {formatDate(t)}
              </Text>
            </group>
          );
        })}
      </group>
    );
  };

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

        {/* Axis at bottom. We'll place it below all chunks, say at y=- (margin.top + maxChunkHeight + margin.bottom/2) */}
        <AxisBottom3D
          xScale={xScale}
          yPosition={-totalHeight + margin.bottom / 2}
          tickCount={5}
        />
      </Canvas>
    </div>
  );
}
