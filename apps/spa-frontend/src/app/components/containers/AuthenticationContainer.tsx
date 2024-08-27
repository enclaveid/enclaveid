import React, { ReactElement, useCallback } from 'react';
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
  const { mutate: mutateAuth, data: userId } =
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

  const trpcUtils = trpc.useUtils();

  const handleSubmit = useCallback(
    async (formData: Record<string, string>) => {
      const encryptedCredentials = await asymmetricEncrypt(
        {
          ...formData,
          b64SessionKey: Buffer.from(getSessionKey()).toString('base64'),
        },
        publicKey,
      );

      mutateAuth(
        {
          encryptedCredentials,
        },
        {
          onSuccess: () => {
            localStorage.setItem('userId', userId);

            trpcUtils.private.authCheck.invalidate().then(() => {
              navigate('/onboarding');
            });
          },
        },
      );
    },
    [publicKey, mutateAuth, navigate, trpcUtils, userId],
  );

  return React.cloneElement(children, { handleSubmit });
}
