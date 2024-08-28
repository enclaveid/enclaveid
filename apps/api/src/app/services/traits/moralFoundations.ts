import {
  MoralFoundationsPartial,
  QuestionnairePart,
  questionnaires,
} from '@enclaveid/shared';

/**
 * See https://moralfoundations.org/questionnaires/ item key file.
 * @param mfq20Answers
 * @param part
 * @returns
 */
function getMfq20PartScores(
  mfq20Answers: Record<string, string>,
  part: QuestionnairePart,
) {
  const { options, questions } = part;

  const scores = Object.entries(mfq20Answers).reduce(
    (acc, [question, answer]) => {
      const questionIndex = questions.indexOf(question);
      const score = options.indexOf(answer);

      let key: keyof MoralFoundationsPartial;
      switch (questionIndex) {
        case 0:
        case 6:
          key = 'careHarm';
          break;
        case 1:
        case 7:
          key = 'fairnessCheating';
          break;
        case 2:
        case 8:
          key = 'loyaltyBetrayal';
          break;
        case 3:
        case 9:
          key = 'authoritySubversion';
          break;
        case 4:
        case 10:
          key = 'sanctityDegradation';
          break;
        case 5:
          if (question === 'Whether or not someone was good at math.') {
            key = 'mathCheck';
          } else if (question === 'It is better to do good than to do bad.') {
            key = 'goodCheck';
          }
          break;
        default:
          throw new Error(
            `Invalid question index: ${questionIndex}: ${question}`,
          );
      }

      acc[key] = acc[key] ? acc[key] + score : score;

      return acc;
    },
    {} as MoralFoundationsPartial,
  );

  return scores;
}

export function getMfq20Scores(mfq20Answers: Record<string, string>) {
  const normalizedScores = questionnaires
    .find((questionnaire) => questionnaire.id === 'MFQ20')
    .parts.map((part, i) =>
      getMfq20PartScores(
        // TODO: do this upstream
        Object.fromEntries(
          Object.entries(mfq20Answers).slice(i * 11, (i + 1) * 11),
        ),
        part,
      ),
    )
    .reduce((acc, partScores) => {
      Object.entries(partScores).forEach(([key, value]) => {
        const normalizedScore = value / 20;
        acc[key] = acc[key] ? acc[key] + normalizedScore : normalizedScore;
      });

      return acc;
    }, {} as MoralFoundationsPartial);

  return normalizedScores;
}
