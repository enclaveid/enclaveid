import { BigFivePartial, questionnaires } from '@enclaveid/shared';

export function getTipiScores(tipiAnswers: Record<string, string>) {
  const reverseScoredItems = [1, 3, 5, 7, 9];

  const { options, questions } = questionnaires.find(
    (questionnaire) => questionnaire.id === 'TIPI',
  ).parts[0];

  const scores = Object.entries(tipiAnswers).reduce(
    (acc, [question, answer]) => {
      const questionIndex = questions.indexOf(question);

      const score = reverseScoredItems.includes(questionIndex)
        ? 8 - options.indexOf(answer)
        : options.indexOf(answer) + 1;

      let key: keyof BigFivePartial;
      switch (questionIndex) {
        case 0:
        case 5:
          key = 'extraversion';
          break;
        case 1:
        case 6:
          key = 'agreeableness';
          break;
        case 2:
        case 7:
          key = 'conscientiousness';
          break;
        case 3:
        case 8:
          key = 'neuroticism';
          break;
        case 4:
        case 9:
          key = 'openness';
          break;
      }

      return {
        ...acc,
        [key]: acc[key] ? (acc[key] + score) / 2 : score,
      };
    },
    {} as BigFivePartial,
  );

  const normalizedScores = Object.entries(scores).reduce(
    (acc, [key, value]) => ({
      ...acc,
      [key]: (value - 1) / 6,
    }),
    {} as BigFivePartial,
  );

  return normalizedScores;
}
