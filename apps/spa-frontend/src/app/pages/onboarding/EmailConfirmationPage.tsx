import { LoadingPage } from '../LoadingPage';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { trpc } from '../../utils/trpc';
import { useEffect } from 'react';

export function EmailConfirmationPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const { mutate: mutateConfirmEmail } =
    trpc.private.confirmEmail.useMutation();

  const navigate = useNavigate();

  // If the token is present, confirm the email
  useEffect(() => {
    if (token) {
      mutateConfirmEmail(
        { token },
        {
          onSuccess: () => {
            navigate('/onboarding');
          },
        },
      );
    }
  }, [token, mutateConfirmEmail, navigate]);

  return <LoadingPage customMessage="Waiting for email confirmation..." />;
}
