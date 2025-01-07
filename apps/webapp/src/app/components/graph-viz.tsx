import React, { useMemo, useState, useCallback, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { GraphVizErrorBoundary } from './graph-viz/graph-viz-error-boundary';
import { Lines } from './graph-viz/lines';
import { NodeMesh } from './graph-viz/node-mesh';
import { SearchBox } from './graph-viz/search-box';

// ----------------------------------
// Data Interfaces
// ----------------------------------
export interface NodeData {
  label: string;
  category: string;
  node_type: 'inferrable' | 'observable';
  description: string;
  start_date: string | Date;
  end_date: string | Date;
  edges: string[];
}

export interface ProcessedNode extends NodeData {
  startDayOffset: number;
  endDayOffset: number;
  yOffset: number;
  color: string;
  dayWidth?: number;
  nodeHeight?: number;
}

export interface GraphVizProps {
  data: NodeData[];
  dayWidth?: number;
  nodeHeight?: number;
  spacing?: number;
  initialZoom?: number;
}

const DEFAULT_NODE_HEIGHT = 5;

// ----------------------------------
// Main Component
// ----------------------------------
export function GraphViz({
  data,
  dayWidth = 5,
  nodeHeight = DEFAULT_NODE_HEIGHT,
  spacing = DEFAULT_NODE_HEIGHT + 0.5,
  initialZoom = 20,
}: GraphVizProps) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const [firstNodeClicked, setFirstNodeClicked] = useState<string | null>(null);

  const [pathEdges, setPathEdges] = useState<Set<string>>(new Set());

  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Process data
  const { parsedNodes, edgesMap } = useMemo(() => {
    if (!data?.length) return { parsedNodes: [], edgesMap: {} };

    const minDate = data
      .map((d) => new Date(d.start_date))
      .reduce((prev, curr) => (curr < prev ? curr : prev));

    const referenceTime = minDate.getTime();

    // Build edges map
    const edges: Record<string, string[]> = {};
    data.forEach((d) => {
      // Ensure an array exists for this node
      edges[d.label] = edges[d.label] || [];

      (d.edges || []).forEach((neighbor) => {
        // Add neighbor to d.label’s list
        edges[d.label].push(neighbor);

        // Also ensure neighbor has an array, then add d.label to neighbor’s list
        edges[neighbor] = edges[neighbor] || [];
        edges[neighbor].push(d.label);
      });
    });

    // Get unique categories and generate colors
    const uniqueCategories = Array.from(new Set(data.map((d) => d.category)));
    const categoryColors: Record<string, string> = {};
    uniqueCategories.forEach((category, index) => {
      const hue = (index / uniqueCategories.length) * 360;
      categoryColors[category] = `hsl(${hue}, 70%, 60%)`;
    });

    // Process and stack nodes
    const byCategory: Record<string, ProcessedNode[]> = {};

    data.forEach((node) => {
      const startTime = new Date(node.start_date).getTime();
      let endTime = new Date(node.end_date).getTime();

      // Ensure we have a minimal timespan
      if (startTime === endTime) {
        endTime = startTime + 1000 * 3600 * 24;
      }

      if (isNaN(startTime) || isNaN(endTime)) {
        console.warn(`Invalid date for node: ${node.label}`);
        return;
      }

      const processedNode: ProcessedNode = {
        ...node,
        startDayOffset: (startTime - referenceTime) / (1000 * 3600 * 24),
        endDayOffset: (endTime - referenceTime) / (1000 * 3600 * 24),
        yOffset: 0,
        color: categoryColors[node.category] || categoryColors.default,
        dayWidth,
        nodeHeight,
      };

      if (!byCategory[node.category]) {
        byCategory[node.category] = [];
      }
      byCategory[node.category].push(processedNode);
    });

    // Stack nodes within categories
    const stacked: ProcessedNode[] = [];
    Object.values(byCategory).forEach((nodes) => {
      // Sort nodes by start date first
      const sortedNodes = nodes.sort(
        (a, b) => a.startDayOffset - b.startDayOffset
      );

      let currentY = 0;
      // Stacking logic: shift yOffset enough to avoid overlaps
      sortedNodes.forEach((node) => {
        while (
          stacked.some(
            (n) =>
              n.category === node.category &&
              n.yOffset === currentY &&
              !(
                node.startDayOffset > n.endDayOffset ||
                node.endDayOffset < n.startDayOffset
              )
          )
        ) {
          currentY += spacing;
        }
        stacked.push({ ...node, yOffset: currentY });
      });
    });

    return { parsedNodes: stacked, edgesMap: edges };
  }, [data, dayWidth, nodeHeight, spacing]);

  // NEW: BFS to find the shortest path between two labels
  const findShortestPath = useCallback(
    (start: string, end: string) => {
      if (!edgesMap || !edgesMap[start] || !edgesMap[end]) return [];
      if (start === end) return [start];

      const queue = [[start]];
      const visited = new Set([start]);

      while (queue.length > 0) {
        const path = queue.shift();
        if (!path) continue;

        const node = path[path.length - 1];
        // If we've reached the end
        if (node === end) return path;

        // Otherwise, explore neighbors
        for (const neighbor of edgesMap[node] || []) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            queue.push([...path, neighbor]);
          }
        }
      }

      return [];
    },
    [edgesMap]
  );

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    setTooltipPos({ x: e.clientX, y: e.clientY });
  }, []);

  const hoveredData = parsedNodes.find((n) => n.label === hoveredNode);

  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (!searchTerm) {
      // Clear highlight if the user deletes the search
      setSelectedNode(null);
      return;
    }
    // Case-insensitive match
    const foundNode = parsedNodes.find((n) =>
      n.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
    if (foundNode) {
      setSelectedNode(foundNode.label);
    } else {
      setSelectedNode(null);
    }
  }, [searchTerm, parsedNodes]);

  return (
    <GraphVizErrorBoundary>
      <div
        style={{ width: '100%', height: '100%', position: 'relative' }}
        onMouseMove={handleMouseMove}
      >
        <SearchBox searchTerm={searchTerm} onSearchTermChange={setSearchTerm} />

        <Canvas
          orthographic
          camera={{
            zoom: initialZoom,
            position: [0, 0, 100],
            near: 0.1,
            far: 1000,
          }}
          style={{ background: '#000000' }}
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
            screenSpacePanning={true}
            zoomToCursor={true}
            target0={new THREE.Vector3(0, 0, 0)}
          />

          <Lines
            nodes={parsedNodes}
            edgesMap={edgesMap}
            hoveredNode={hoveredNode}
            selectedNode={selectedNode}
            dayWidth={dayWidth}
            pathEdges={pathEdges}
          />

          {parsedNodes.map((node) => (
            <NodeMesh
              key={node.label}
              node={node}
              hoveredNode={hoveredNode}
              selectedNode={selectedNode}
              edgesMap={edgesMap}
              onHover={setHoveredNode}
              onSelect={setSelectedNode}
              onFirstClick={setFirstNodeClicked}
              firstNodeClicked={firstNodeClicked}
              findPath={findShortestPath}
              onUpdatePathEdges={setPathEdges}
            />
          ))}
        </Canvas>

        {hoveredNode && hoveredData && (
          <div
            style={{
              position: 'absolute',
              left: tooltipPos.x + 10,
              top: tooltipPos.y + 10,
              padding: '6px 10px',
              background: 'rgba(0, 0, 0, 0.75)',
              color: '#fff',
              borderRadius: 4,
              pointerEvents: 'none',
              fontSize: '0.85rem',
              whiteSpace: 'nowrap',
              zIndex: 1000,
            }}
          >
            <div style={{ fontWeight: 'bold' }}>{hoveredData.label}</div>
            <div>Description: {hoveredData.description}</div>
            <div>Category: {hoveredData.category}</div>
            <div>
              {`From ${new Date(hoveredData.start_date).toLocaleDateString()}`}
            </div>
            <div>
              {`To   ${new Date(hoveredData.end_date).toLocaleDateString()}`}
            </div>
          </div>
        )}
      </div>
    </GraphVizErrorBoundary>
  );
}
