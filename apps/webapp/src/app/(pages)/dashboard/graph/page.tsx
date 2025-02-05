'use client';

import { GraphVizFileProvider } from '../../../components/graph-viz/graph-viz-file-context';
import { GraphVizRouter } from '../../../components/graph-viz/graph-viz-router';

export default function Graph() {
  return (
    <GraphVizFileProvider>
      <GraphVizRouter />
    </GraphVizFileProvider>
  );
}
