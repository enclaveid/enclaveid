import { describe, expect, it } from 'bun:test';
import { getMfq20Scores } from './moralFoundations';
import { questionnaires } from '@enclaveid/shared';

const questionnaireParts = questionnaires.find((q) => q.id === 'MFQ20').parts;

const maxP1 = questionnaireParts[0].options[5];
const maxP2 = questionnaireParts[1].options[5];

const answers = {
  'Whether or not someone suffered emotionally.': maxP1,
  'Whether or not some people were treated differently than others.': maxP1,
  'Whether or not someone’s action showed love for his or her country': maxP1,
  'Whether or not someone showed a lack of respect for authority.': maxP1,
  'Whether or not someone violated standards of purity and decency.': maxP1,
  'Whether or not someone was good at math.': maxP1,
  'Whether or not someone cared for someone weak or vulnerable': maxP1,
  'Whether or not someone acted unfairly': maxP1,
  'Whether or not someone did something to betray his or her group': maxP1,
  'Whether or not someone conformed to the traditions of society': maxP1,
  'Whether or not someone did something disgusting': maxP1,
  'Compassion for those who are suffering is the most crucial virtue.': maxP2,
  'When the government makes laws, the number one principle should be ensuring the good of the people.':
    maxP2,
  'I am proud of my country’s history.': questionnaireParts[1].options[5],
  'Respect for authority is something all children need to learn.': maxP2,
  'People should not do things that are disgusting, even if no one is harmed.':
    maxP2,
  'It is better to do good than to do bad.': questionnaireParts[1].options[5],
  'One of the worst things a person could do is hurt a defenseless animal.':
    maxP2,
  'Justice is the most important requirement for a society.': maxP2,
  'People should be loyal to their family members, even when they have done something wrong.':
    maxP2,
  'Men and women each have different roles to play in society.': maxP2,
  'I would call some acts wrong on the grounds that they are unnatural.': maxP2,
};

describe('moralFoundations', () => {
  it('should calculate the moral foundations scores', () => {
    const scores = getMfq20Scores(answers);

    expect(scores).toEqual({
      careHarm: 1,
      fairnessCheating: 1,
      loyaltyBetrayal: 1,
      authoritySubversion: 1,
      sanctityDegradation: 1,
      mathCheck: 0.25,
      goodCheck: 0.25,
    });
  });
});
