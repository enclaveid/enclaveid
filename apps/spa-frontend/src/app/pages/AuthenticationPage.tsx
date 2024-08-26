import { LoginForm } from '../components/auth/LoginForm';
import { SignupForm } from '../components/auth/SignupForm';
import {
  AuthenticationContainer,
  AuthenticationType,
} from '../components/containers/AuthenticationContainer';

export function AuthenticationPage({
  authenticationType,
}: {
  authenticationType: AuthenticationType;
}) {
  return (
    <AuthenticationContainer authenticationType={authenticationType}>
      {authenticationType === 'login' ? <LoginForm /> : <SignupForm />}
    </AuthenticationContainer>
  );
}
