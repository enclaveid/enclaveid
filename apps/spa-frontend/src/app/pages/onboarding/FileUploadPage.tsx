import { FileUploadForm } from '../../components/onboarding/FileUploadForm';
import { FileUploadContainer } from '../../components/containers/FileUploadContainer';
import { RequireAuth } from '../../providers/AuthProvider';

export function FileUploadPage() {
  return (
    <RequireAuth>
      <FileUploadContainer>
        <FileUploadForm />
      </FileUploadContainer>
    </RequireAuth>
  );
}
