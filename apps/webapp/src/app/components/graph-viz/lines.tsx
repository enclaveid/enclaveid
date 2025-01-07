import React, { useMemo } from 'react';
import * as THREE from 'three';
import { MeshLineComponent } from './mesh-line-component';

export const Lines = React.memo(
  ({
    nodes,
    edgesMap,
    hoveredNode,
    selectedNode,
    dayWidth,
    pathEdges, // new
  }: {
    nodes: any[];
    edgesMap: Record<string, string[]>;
    hoveredNode: string | null;
    selectedNode: string | null;
    dayWidth: number;
    pathEdges: Set<string>; // new
  }) => {
    const lineGeometries = useMemo(() => {
      const geometries: Array<{
        points: THREE.Vector3[];
        key: string;
        isHoveredOrSelected: boolean;
        isPathEdge: boolean;
      }> = [];

      const drawnPairs = new Set<string>();

      nodes.forEach((node) => {
        const connectedLabels = edgesMap[node.label] || [];
        connectedLabels.forEach((cLabel) => {
          const target = nodes.find((n) => n.label === cLabel);
          if (!target) return;

          const pairKey = [node.label, cLabel].sort().join(':');
          if (drawnPairs.has(pairKey)) return;
          drawnPairs.add(pairKey);

          // Original highlight logic:
          const lineIsHovered =
            hoveredNode &&
            (node.label === hoveredNode || target.label === hoveredNode);
          const lineIsSelected =
            selectedNode &&
            (node.label === selectedNode || target.label === selectedNode);

          const isHoveredOrSelected = lineIsHovered || lineIsSelected;

          // Compute positions for line
          const startX =
            node.startDayOffset * dayWidth +
            ((node.endDayOffset - node.startDayOffset) * dayWidth) / 2;
          const endX =
            target.startDayOffset * dayWidth +
            ((target.endDayOffset - target.startDayOffset) * dayWidth) / 2;

          const isInPath = pathEdges.has(pairKey);

          geometries.push({
            points: [
              new THREE.Vector3(startX, node.yOffset, 0),
              new THREE.Vector3(endX, target.yOffset, 0),
            ],
            key: pairKey,
            isHoveredOrSelected: Boolean(isHoveredOrSelected),
            isPathEdge: isInPath,
          });
        });
      });

      return geometries;
    }, [nodes, edgesMap, hoveredNode, selectedNode, dayWidth, pathEdges]);

    return (
      <group>
        {lineGeometries.map(
          ({ points, key, isHoveredOrSelected, isPathEdge }) => {
            // Always render if it's part of the path or if it's hovered/selected
            if (!isPathEdge && !isHoveredOrSelected) return null;

            return (
              <MeshLineComponent
                key={key}
                points={points.map((v) => [v.x, v.y, v.z])}
                color={isPathEdge ? 'red' : 'white'}
                lineWidth={0.01}
                isHighlighted={true}
              />
            );
          }
        )}
      </group>
    );
  }
);

Lines.displayName = 'Lines';
