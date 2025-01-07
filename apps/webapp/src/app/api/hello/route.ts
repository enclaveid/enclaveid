import { NextResponse } from 'next/server';
import createLayout from 'ngraph.forcelayout';
import createGraph from 'ngraph.graph';

export async function GET(request: Request) {
  try {
    // Create graph
    const graph = createGraph();

    // Add 100k nodes
    for (let i = 0; i < 100000; i++) {
      graph.addNode(i);
    }

    // Add 200k random edges
    for (let i = 0; i < 200000; i++) {
      const source = Math.floor(Math.random() * 100000);
      const target = Math.floor(Math.random() * 100000);
      if (source !== target) {
        graph.addLink(source, target);
      }
    }

    // Create and configure layout
    const layout = createLayout(graph, {
      springLength: 30,
      springCoefficient: 0.0008,
      gravity: -1.2,
      theta: 0.8,
      dragCoefficient: 0.02,
      timeStep: 20,
    });

    // Run iterations
    console.log('Computing layout...');
    const iterations = 100; // Adjust based on your needs
    for (let i = 0; i < iterations; i++) {
      const stability = layout.step();
      if (i % 10 === 0) {
        console.log(
          `Completed ${i}/${iterations} iterations. Stability: ${stability}`
        );
      }
    }

    // Get positions
    const positions = [];
    graph.forEachNode((node) => {
      const pos = layout.getNodePosition(node.id);
      positions[node.id] = {
        x: pos.x,
        y: pos.y,
        z: pos.z,
      };
    });

    // Clean up
    layout.dispose();

    return NextResponse.json({ positions });
  } catch (error) {
    console.error('Error computing layout:', error);
    return NextResponse.json(
      { error: 'Failed to compute layout' },
      { status: 500 }
    );
  }
}
