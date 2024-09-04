import { ReactElement, useCallback, useEffect, useState } from 'react';
import { StepFormProps } from '../onboarding/StepForm';
import React from 'react';
import { trpc } from '../../utils/trpc';
import { Questionnaire, questionnaires } from '@enclaveid/shared';
import { useOnboardingSkips } from '../../providers/OnboardingSkipsProvider';
import { useNavigate } from 'react-router-dom';

export function QuestionnaireContainer({
  children,
}: {
  children: ReactElement<StepFormProps>;
}) {
  const { skips } = useOnboardingSkips();
  const navigate = useNavigate();

  const onSkipAll = useCallback(() => {
    skips['/onboarding/questionnaire'].onSkip();
    navigate('/dashboard', { replace: true });
  }, [skips, navigate]);

  const { data: onboardingStatus } =
    trpc.private.getOnboardingStatus.useQuery();

  const { mutate: createbigFiveMutation } =
    trpc.private.createbigFive.useMutation();
  const { mutate: createMoralFoundationsMutation } =
    trpc.private.createMoralFoundations.useMutation();

  const [todoQuestionnaire, setTodoQuestionnaire] =
    React.useState<Questionnaire>(questionnaires[0]);

  const [skippedBigFive, setSkippedBigFive] = useState(false);
  const [skippedMoralFoundations, setSkippedMoralFoundations] = useState(false);
  const [onSkip, setOnSkip] = useState<() => void>(() => void 0);

  useEffect(() => {
    if (!onboardingStatus) {
      return;
    }

    if (!onboardingStatus.isBigFiveComplete && !skippedBigFive) {
      setTodoQuestionnaire(questionnaires.find((q) => q.id === 'TIPI'));
      setOnSkip(() => {
        return () => setSkippedBigFive(true);
      });
    } else if (
      !onboardingStatus.isMoralFoundationsComplete &&
      !skippedMoralFoundations
    ) {
      setTodoQuestionnaire(questionnaires.find((q) => q.id === 'MFQ20'));
      setOnSkip(() => {
        return () => setSkippedMoralFoundations(true);
      });
    } else {
      onSkipAll();
    }
  }, [onboardingStatus, skippedBigFive, skippedMoralFoundations, onSkipAll]);

  const trpcUtils = trpc.useUtils();

  const onFinished = useCallback(
    (answers) => {
      if (todoQuestionnaire?.id === 'TIPI') {
        createbigFiveMutation(
          { answers },
          {
            onSuccess: () => {
              trpcUtils.private.getOnboardingStatus.invalidate();
            },
          },
        );
      } else if (todoQuestionnaire?.id === 'MFQ20') {
        createMoralFoundationsMutation(
          { answers },
          {
            onSuccess: () => {
              trpcUtils.private.getOnboardingStatus.invalidate();
            },
          },
        );
      }
    },
    [
      trpcUtils,
      todoQuestionnaire,
      createbigFiveMutation,
      createMoralFoundationsMutation,
    ],
  );

  return React.cloneElement(children, {
    questionnaire: todoQuestionnaire,
    onFinished,
    onSkip,
  });
}
