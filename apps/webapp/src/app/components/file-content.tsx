'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface FileContextType {
  fileData: any | null;
  setFileData: (data: any) => void;
}

const FileContext = createContext<FileContextType | undefined>(undefined);

export function FileProvider({ children }: { children: ReactNode }) {
  const [fileData, setFileData] = useState<any | null>(null);

  return (
    <FileContext.Provider value={{ fileData, setFileData }}>
      {children}
    </FileContext.Provider>
  );
}

export function useFileData() {
  const context = useContext(FileContext);
  if (undefined === context) {
    throw new Error('useFileData must be used within a FileProvider');
  }
  return context;
}
