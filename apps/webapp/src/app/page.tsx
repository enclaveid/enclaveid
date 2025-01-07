'use client';

import { FileUploader } from './components/file-uploader';
import { useFileData } from './components/file-content';
import { GraphViz } from './components/graph-viz';

export default function Index() {
  const { fileData } = useFileData();

  return fileData ? (
    <div style={{ width: '100vw', height: '100vh' }}>
      <GraphViz data={fileData} />
    </div>
  ) : (
    <FileUploader />
  );
}
