import { useEffect, useState } from 'react';
import { trpc } from '../utils/trpc';

export function useDisplayNameAvailable(displayName: string) {
  const [status, setStatus] = useState<'loading' | 'available' | 'unavailable'>(
    'loading',
  );

  const displayNameAvailableQuery = trpc.public.isDisplayNameAvailable.useQuery(
    { displayName },
    { enabled: false },
  );

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      displayNameAvailableQuery.refetch();
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [displayName, displayNameAvailableQuery]);

  useEffect(() => {
    if (displayNameAvailableQuery.isLoading) {
      setStatus('loading');
    } else if (displayNameAvailableQuery.isSuccess) {
      setStatus(displayNameAvailableQuery.data ? 'available' : 'unavailable');
    }
  }, [
    displayNameAvailableQuery.isLoading,
    displayNameAvailableQuery.isSuccess,
    displayNameAvailableQuery.data,
  ]);

  return status;
}
