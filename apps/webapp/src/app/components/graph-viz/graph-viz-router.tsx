import { useGraphVizFileData } from './graph-viz-file-context';

import { GraphViz } from './graph-viz';
import { GraphVizFileLoader } from './graph-viz-file-loader';

export function GraphVizRouter() {
  const { chunkData, nodeData } = useGraphVizFileData();

  return chunkData && nodeData ? (
    <GraphViz chunks={chunkData} nodes={nodeData} />
  ) : (
    <GraphVizFileLoader />
  );
}
