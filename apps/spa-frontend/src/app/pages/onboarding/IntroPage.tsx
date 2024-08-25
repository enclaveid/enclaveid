import { CreateProfile } from '../../components/onboarding/CreateProfile';
import { RequireAuth } from '../../providers/AuthProvider';

export function IntroPage() {
  return (
    <RequireAuth>
      <CreateProfile />
    </RequireAuth>
  );
}
