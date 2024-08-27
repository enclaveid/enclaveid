import { createContext, useContext, useMemo, useState } from 'react';

type OnboardingPaths =
  | '/onboarding/purposeSelection'
  | '/onboarding/fileUpload'
  | '/onboarding/questionnaire';

type OnboardingSkipsContextType = {
  skips: Record<OnboardingPaths, { onSkip: () => void; skipped: boolean }>;
} & { reset: () => void };

export const OnboardingSkipsContext = createContext<OnboardingSkipsContextType>(
  {
    skips: {
      '/onboarding/purposeSelection': { onSkip: () => void 0, skipped: false },
      '/onboarding/fileUpload': { onSkip: () => void 0, skipped: false },
      '/onboarding/questionnaire': { onSkip: () => void 0, skipped: false },
    },
    reset: () => void 0,
  },
);

export function OnboardingSkipsProvider(props: { children: React.ReactNode }) {
  const [skipFileUpload, setSkipFileUpload] = useState(false);
  const [skipQuestionnaire, setSkipQuestionnaire] = useState(false);

  const value = useMemo(() => {
    return {
      skips: {
        '/onboarding/purposeSelection': {
          onSkip: () => void 0,
          skipped: false,
        },
        '/onboarding/fileUpload': {
          onSkip: () => setSkipFileUpload(true),
          skipped: skipFileUpload,
        },
        '/onboarding/questionnaire': {
          onSkip: () => setSkipQuestionnaire(true),
          skipped: skipQuestionnaire,
        },
      },
      reset: () => {
        setSkipFileUpload(false);
        setSkipQuestionnaire(false);
      },
    };
  }, [skipFileUpload, skipQuestionnaire]);

  return (
    <OnboardingSkipsContext.Provider value={value}>
      {props.children}
    </OnboardingSkipsContext.Provider>
  );
}

export function useOnboardingSkips() {
  return useContext(OnboardingSkipsContext);
}
