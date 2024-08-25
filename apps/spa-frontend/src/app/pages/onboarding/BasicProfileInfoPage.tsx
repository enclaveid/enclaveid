import { CreateProfileForm } from '../../components/onboarding/CreateProfileForm';
import { RequireAuth } from '../../providers/AuthProvider';

export function BasicProfileInfoPage() {
  return (
    <RequireAuth>
      <CreateProfileForm />
    </RequireAuth>
  );
}
