import { createContext, useContext, useEffect, useState } from 'react';
import { OnboardingStatus } from '../types/trpc';
import { trpc } from '../utils/trpc';

type OnboardingStatusContextType = {
  onboardingStatus?: OnboardingStatus;
  refreshOnboardingStatus: () => void;
};

export const OnboardingStatusContext =
  createContext<OnboardingStatusContextType>({
    onboardingStatus: null,
    refreshOnboardingStatus: () => void 0,
  });

export function OnboardingStatusProvider(props: { children: React.ReactNode }) {
  const [onboardingStatus, setOnboardingStatus] =
    useState<OnboardingStatus>(null);

  const onboardingStatusQuery = trpc.private.getOnboardingStatus.useQuery();
  const trpcUtils = trpc.useUtils();

  const refreshOnboardingStatus = () => {
    trpcUtils.private.getOnboardingStatus.invalidate();
  };

  useEffect(() => {
    if (onboardingStatusQuery.data) {
      setOnboardingStatus(onboardingStatusQuery.data);
    }
  }, [onboardingStatusQuery.data]);

  return (
    <OnboardingStatusContext.Provider
      value={{ onboardingStatus, refreshOnboardingStatus }}
    >
      {props.children}
    </OnboardingStatusContext.Provider>
  );
}

export function useOnboardingStatus() {
  const context = useContext(OnboardingStatusContext);
  if (!context) {
    throw new Error(
      'useOnboardingStatus must be used within an OnboardingStatusProvider',
    );
  }
  return context;
}
