import { ReactElement, useCallback, useEffect } from 'react';
import { StepFormProps } from '../onboarding/StepForm';
import React from 'react';
import { trpc } from '../../utils/trpc';
import { QuestionnaireId, questionnaires } from '@enclaveid/shared';

export function QuestionnaireContainer({
  onSkipAll,
  children,
}: {
  onSkipAll: () => void;
  children: ReactElement<StepFormProps>;
}) {
  const personalityQuery = trpc.private.getPersonalityTraits.useQuery();
  const politicsQuery = trpc.private.getPoliticsTraits.useQuery();

  const createbigFiveMutation = trpc.private.createbigFive.useMutation();
  const createMoralFoundationsMutation =
    trpc.private.createMoralFoundations.useMutation();

  const [todoQuestionnaires, setTodoQuestionnaires] = React.useState<
    QuestionnaireId[]
  >(questionnaires.map((questionnaire) => questionnaire.id));

  useEffect(() => {
    if (personalityQuery.error || politicsQuery.error) return;

    if (personalityQuery.isLoading || politicsQuery.isLoading) return;

    setTodoQuestionnaires(
      [
        !personalityQuery.data.bigfive ? 'TIPI' : undefined,
        !politicsQuery.data.moralFoundations ? 'MFQ20' : undefined,
      ].filter((id) => id) as QuestionnaireId[],
    );
  }, [
    personalityQuery.data,
    personalityQuery.error,
    personalityQuery.isLoading,
    politicsQuery.data,
    politicsQuery.error,
    politicsQuery.isLoading,
  ]);

  useEffect(() => {
    if (todoQuestionnaires.length === 0) {
      onSkipAll();
    }
  }, [todoQuestionnaires, onSkipAll]);

  const onFinished = useCallback(
    (answers) => {
      if (todoQuestionnaires[0] === 'TIPI') {
        createbigFiveMutation.mutateAsync(
          { answers },
          {
            onSuccess: () => {
              personalityQuery.refetch();
            },
          },
        );
      } else if (todoQuestionnaires[0] === 'MFQ20') {
        createMoralFoundationsMutation.mutateAsync(
          { answers },
          {
            onSuccess: () => {
              politicsQuery.refetch();
            },
          },
        );
      }
    },
    [
      todoQuestionnaires,
      createbigFiveMutation,
      personalityQuery,
      createMoralFoundationsMutation,
      politicsQuery,
    ],
  );

  return React.cloneElement(children, {
    questionnaire:
      questionnaires.find(
        (questionnaire) => questionnaire.id === todoQuestionnaires[0],
      ) || questionnaires[0],
    onFinished,
    onSkip: onSkipAll,
  });
}
