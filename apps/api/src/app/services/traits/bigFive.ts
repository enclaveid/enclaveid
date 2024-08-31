import { BigFivePartial, questionnaires } from '@enclaveid/shared';

export function getTipiScores(tipiAnswers: Record<string, string>) {
  const reverseScoredItems = [1, 3, 5, 7, 9];

  const { options, questions } = questionnaires.find(
    (questionnaire) => questionnaire.id === 'TIPI',
  ).parts[0];

  // Order the tipiAnswers according to the questions array
  const orderedAnswers = questions.map((question) => tipiAnswers[question]);

  const scores = orderedAnswers.reduce((acc, answer, index) => {
    const score = reverseScoredItems.includes(index)
      ? options.length - options.indexOf(answer) - 1
      : options.indexOf(answer);

    let key: keyof BigFivePartial;
    switch (index) {
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
      [key]: acc[key] ? acc[key] + score : score,
    };
  }, {} as BigFivePartial);

  const normalizedScores = Object.entries(scores).reduce(
    (acc, [key, value]) => ({
      ...acc,
      [key]: value / ((options.length - 1) * 2),
    }),
    {} as BigFivePartial,
  );

  // Validate that the Big Five traits are within the expected range
  Object.values(normalizedScores).forEach((value) => {
    if (value < 0 || value > 1) {
      throw new Error(
        `Big Five traits must be between 0 and 1: ${JSON.stringify(
          normalizedScores,
        )}`,
      );
    }
  });

  return {
    ...normalizedScores,
    // Invert the score for neuroticism since TIPI originally has "emotional stability" which is a positive trait
    neuroticism: 1 - normalizedScores.neuroticism,
  };
}
