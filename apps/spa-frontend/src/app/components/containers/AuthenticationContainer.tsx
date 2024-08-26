import React, { ReactElement, useCallback, useEffect } from 'react';
import { trpc } from '../../utils/trpc';
import { asymmetricEncrypt } from '../../utils/crypto/asymmetricBrowser';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAwsNitroAttestation } from '../../hooks/attestation/useAwsNitroAttestation';
import { getSessionKey } from '../../utils/crypto/symmetricBrowser';
import { Buffer } from 'buffer';
import { LoginFormProps } from '../auth/LoginForm';
import { SignupFormProps } from '../auth/SignupForm';

export type AuthenticationType = 'login' | 'signup';

export function AuthenticationContainer({
  children,
  authenticationType,
}: {
  children: ReactElement<LoginFormProps | SignupFormProps>;
  authenticationType: AuthenticationType;
}) {
  const authCheck = trpc.private.authCheck.useQuery();
  const authMutation =
    authenticationType === 'login'
      ? trpc.public.login.useMutation()
      : trpc.public.signup.useMutation();

  // TODO change to Azure
  const { publicKey, error } = useAwsNitroAttestation();
  const navigate = useNavigate();
  const location = useLocation();

  // In the login case, we might want to redirect the user to the page they were trying to access
  const { from } = location.state || {
    from: { pathname: '/dashboard/personality' },
  };

  const handleSubmit = useCallback(
    async (formData: Record<string, string>) => {
      const encryptedCredentials = await asymmetricEncrypt(
        {
          ...formData,
          b64SessionKey: Buffer.from(getSessionKey()).toString('base64'),
        },
        publicKey,
      );

      authMutation.mutate({
        encryptedCredentials,
      });
    },
    [publicKey, authMutation],
  );

  useEffect(() => {
    if (authMutation.isSuccess) {
      // Save the user's id in local storage
      localStorage.setItem('userId', authMutation.data);

      authCheck.refetch().then(() => {
        const navigateTo =
          authenticationType === 'login'
            ? (from.pathname ?? '/dashboard')
            : '/fileUpload';

        navigate(navigateTo);
      });
    }
  }, [
    authMutation.isSuccess,
    navigate,
    from,
    authenticationType,
    authCheck,
    authMutation.data,
  ]);

  return React.cloneElement(children, { handleSubmit });
}
