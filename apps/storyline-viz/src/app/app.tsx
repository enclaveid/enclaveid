import { useFileData } from './FileContext';
import { FileUploader } from './FileUploader';
import { Storyline } from './Storyline';

export function App() {
  const { fileData } = useFileData();

  return fileData ? <Storyline data={fileData} /> : <FileUploader />;
}
