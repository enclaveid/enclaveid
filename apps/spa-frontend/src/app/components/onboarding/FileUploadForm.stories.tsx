import { FileUploadForm } from './FileUploadForm';

export default {
  title: 'Components/FileUploadForm',
  component: FileUploadForm,
};

export const Default = () => (
  <FileUploadForm uploadUrl="https://example.com/upload" />
);
