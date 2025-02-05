import { createContext, useContext, useState, ReactNode } from 'react';

interface GraphVizFileContextType {
  chunkData: any | null;
  nodeData: any | null;
  setChunkData: (data: any) => void;
  setNodeData: (data: any) => void;
}

const GraphVizFileContext = createContext<GraphVizFileContextType | undefined>(
  undefined
);

export function GraphVizFileProvider({ children }: { children: ReactNode }) {
  const [chunkData, setChunkData] = useState<any | null>(null);
  const [nodeData, setNodeData] = useState<any | null>(null);

  return (
    <GraphVizFileContext.Provider
      value={{ chunkData, nodeData, setChunkData, setNodeData }}
    >
      {children}
    </GraphVizFileContext.Provider>
  );
}

export function useGraphVizFileData() {
  const context = useContext(GraphVizFileContext);
  if (undefined === context) {
    throw new Error(
      'useGraphVizFileData must be used within a GraphVizFileProvider'
    );
  }
  return context;
}
