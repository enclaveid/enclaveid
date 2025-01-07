import React, { useCallback, useMemo } from 'react';
import * as THREE from 'three';
import { ProcessedNode } from '../graph-viz';

export const NodeMesh = React.memo(
  ({
    node,
    hoveredNode,
    selectedNode,
    edgesMap,
    onHover,
    onSelect,
    onFirstClick,
    firstNodeClicked,
    findPath,
    onUpdatePathEdges,
  }: {
    node: ProcessedNode;
    hoveredNode: string | null;
    selectedNode: string | null;
    edgesMap: Record<string, string[]>;
    onHover: (label: string | null) => void;
    onSelect: (label: string) => void;
    onFirstClick: (label: string | null) => void;
    firstNodeClicked: string | null;
    findPath: (start: string, end: string) => string[];
    onUpdatePathEdges: (edges: Set<string>) => void;
  }) => {
    const startX = node.startDayOffset * (node.dayWidth || 1);
    const endX = node.endDayOffset * (node.dayWidth || 1);
    const width = endX - startX;
    const xPos = startX + width / 2;

    // Check if this node is highlighted by either hover or selection
    const isHighlighted = useMemo(() => {
      // If hoveredNode or selectedNode is 'node.label' itself
      const isSelfHovered = node.label === hoveredNode;
      const isSelfSelected = node.label === selectedNode;

      // If hoveredNode or selectedNode is in edgesMap connecting to this node
      const isConnectedToHovered =
        hoveredNode && edgesMap[hoveredNode]?.includes(node.label);
      const isConnectedToSelected =
        selectedNode && edgesMap[selectedNode]?.includes(node.label);

      return (
        isSelfHovered ||
        isSelfSelected ||
        isConnectedToHovered ||
        isConnectedToSelected
      );
    }, [node.label, hoveredNode, selectedNode, edgesMap]);

    const geometry = useMemo(() => {
      if (node.node_type === 'inferrable') {
        const shape = new THREE.Shape();
        const r = 0.3;
        const halfW = width / 2;
        const halfH = (node.nodeHeight || 1) / 2;

        shape.moveTo(-halfW + r, halfH);
        shape.lineTo(halfW - r, halfH);
        shape.quadraticCurveTo(halfW, halfH, halfW, halfH - r);
        shape.lineTo(halfW, -halfH + r);
        shape.quadraticCurveTo(halfW, -halfH, halfW - r, -halfH);
        shape.lineTo(-halfW + r, -halfH);
        shape.quadraticCurveTo(-halfW, -halfH, -halfW, -halfH + r);
        shape.lineTo(-halfW, halfH - r);
        shape.quadraticCurveTo(-halfW, halfH, -halfW + r, halfH);

        return new THREE.ShapeGeometry(shape);
      }
      return new THREE.BoxGeometry(width, node.nodeHeight || 1, 0.1);
    }, [node.node_type, width, node.nodeHeight]);

    const handleClick = useCallback(() => {
      onSelect(node.label);

      if (!firstNodeClicked) {
        // If no node has been selected yet
        onFirstClick(node.label);
      } else {
        // We already have one node selected, so let's find the path
        // between that node and this newly clicked node.
        if (firstNodeClicked !== node.label) {
          const path = findPath(firstNodeClicked, node.label);
          if (path.length === 0) {
            console.warn('No path found between', firstNodeClicked, node.label);
          } else {
            console.log('path', path);
            // 1) setPathNodes(path)
            // 2) build edges set
            const edgesInPath: string[] = [];
            for (let i = 0; i < path.length - 1; i++) {
              edgesInPath.push([path[i], path[i + 1]].sort().join(':'));
            }
            // 3) update pathEdges right here,
            //    which you can pass down from GraphD3Viz as a prop:
            onUpdatePathEdges(new Set(edgesInPath));
          }
        }
        // Then reset firstNodeClicked
        onFirstClick(node.label);
      }
    }, [
      node.label,
      onSelect,
      firstNodeClicked,
      onFirstClick,
      findPath,
      onUpdatePathEdges,
    ]);

    return (
      <mesh
        position={[xPos, node.yOffset, 0]}
        geometry={geometry}
        onPointerOver={() => onHover(node.label)}
        onPointerOut={() => onHover(null)}
        onClick={handleClick}
      >
        {/* {node.node_type === 'inferrable' && (
          <lineSegments>
            <edgesGeometry args={[geometry]} />
            <lineBasicMaterial color="white" linewidth={1} />
          </lineSegments>
        )} */}
        <meshBasicMaterial
          color={node.color}
          transparent
          // Slightly increase opacity if highlighted, or reduce if not
          opacity={isHighlighted ? 1 : 0.6}
        />
      </mesh>
    );
  }
);
NodeMesh.displayName = 'NodeMesh';
