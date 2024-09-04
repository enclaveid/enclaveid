import { createContext, useState } from 'react';
import { OnboardingStatus } from '../types/trpc';
import { trpc } from '../utils/trpc';

type OnboardingStatusContextType = {
  onboardingStatus: OnboardingStatus;
  setOnboardingStatus: (status: OnboardingStatus) => void;
};

export const OnboardingStatusContext =
  createContext<OnboardingStatusContextType>({
    onboardingStatus: null,
    setOnboardingStatus: () => {},
  });

export function OnboardingStatusProvider(props: { children: React.ReactNode }) {
  const [onboardingStatus, setOnboardingStatus] =
    useState<OnboardingStatus>(null);

  const onboardingStatusQuery = trpc.private.getOnboardingStatus.useQuery();

  return (
    <OnboardingStatusContext.Provider
      value={{ onboardingStatus, setOnboardingStatus }}
    >
      {props.children}
    </OnboardingStatusContext.Provider>
  );
}
