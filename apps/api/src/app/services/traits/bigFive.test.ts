import { describe, expect, it } from 'bun:test';

import { getTipiScores } from './bigFive';

describe('getTipiScores', () => {
  it('should return the correct scores', () => {
    const scores = getTipiScores({
      'I see myself as extraverted, enthusiastic.': 'Agree strongly',
      'I see myself as critical, quarrelsome.': 'Disagree strongly',
      'I see myself as dependable, self-disciplined.': 'Disagree strongly',
      'I see myself as anxious, easily upset.': 'Disagree strongly',
      'I see myself as open to new experiences, complex.': 'Disagree strongly',
      'I see myself as reserved, quiet.': 'Disagree strongly',
      'I see myself as sympathetic, warm.': 'Agree strongly',
      'I see myself as disorganized, careless.': 'Agree strongly',
      'I see myself as calm, emotionally stable.': 'Agree strongly',
      'I see myself as conventional, uncreative.': 'Disagree strongly',
    });
    expect(scores).toEqual({
      openness: 0.5,
      conscientiousness: 0,
      extraversion: 1,
      agreeableness: 1,
      neuroticism: 0,
    });
  });
});
