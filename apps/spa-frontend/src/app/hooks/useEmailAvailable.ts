import { useEffect, useState } from 'react';
import { trpc } from '../utils/trpc';

export function useEmailAvailable(email: string) {
  const [status, setStatus] = useState<'loading' | 'available' | 'unavailable'>(
    'loading',
  );

  const emailAvailableQuery = trpc.public.isEmailAvailable.useQuery(
    { email },
    { enabled: false },
  );

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      emailAvailableQuery.refetch();
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [email, emailAvailableQuery]);

  useEffect(() => {
    if (emailAvailableQuery.isLoading) {
      setStatus('loading');
    } else if (emailAvailableQuery.isSuccess) {
      setStatus(emailAvailableQuery.data ? 'available' : 'unavailable');
    }
  }, [
    emailAvailableQuery.isLoading,
    emailAvailableQuery.isSuccess,
    emailAvailableQuery.data,
  ]);

  return status;
}
