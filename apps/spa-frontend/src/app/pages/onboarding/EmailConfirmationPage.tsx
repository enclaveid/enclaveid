import { LoadingPage } from '../LoadingPage';
import { Navigate, useSearchParams } from 'react-router-dom';
import { trpc } from '../../utils/trpc';
import { useEffect } from 'react';

export function EmailConfirmationPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  console.log('token', token);

  const { mutate: mutateConfirmEmail, isSuccess } =
    trpc.private.confirmEmail.useMutation();

  useEffect(() => {
    if (token) {
      mutateConfirmEmail({ token });
    }
  }, [token, mutateConfirmEmail]);

  return isSuccess ? (
    <Navigate to="/onboarding" replace />
  ) : (
    <LoadingPage customMessage="Waiting for email confirmation..." />
  );
}
