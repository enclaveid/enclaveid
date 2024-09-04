import { describe, expect, it } from 'bun:test';
import { getMfq20Scores } from './moralFoundations';
import { questionnaires } from '@enclaveid/shared';

const questionnaireParts = questionnaires.find((q) => q.id === 'MFQ20').parts;

const maxP1 = questionnaireParts[0].options[5];
const maxP2 = questionnaireParts[1].options[5];

const minP1 = questionnaireParts[0].options[0];
const minP2 = questionnaireParts[1].options[0];

describe('getMfq20Scores', () => {
  it('should calculate the moral foundations scores 1', () => {
    const scores = getMfq20Scores({
      'Whether or not someone suffered emotionally.': minP1,
      'Whether or not some people were treated differently than others.': maxP1,
      'Whether or not someone’s action showed love for his or her country':
        maxP1,
      'Whether or not someone showed a lack of respect for authority.': maxP1,
      'Whether or not someone violated standards of purity and decency.': maxP1,
      'Whether or not someone was good at math.': maxP1,
      'Whether or not someone cared for someone weak or vulnerable': minP1,
      'Whether or not someone acted unfairly': maxP1,
      'Whether or not someone did something to betray his or her group': maxP1,
      'Whether or not someone conformed to the traditions of society': maxP1,
      'Whether or not someone did something disgusting': maxP1,
      'Compassion for those who are suffering is the most crucial virtue.':
        minP2,
      'When the government makes laws, the number one principle should be ensuring the good of the people.':
        maxP2,
      'I am proud of my country’s history.': questionnaireParts[1].options[5],
      'Respect for authority is something all children need to learn.': maxP2,
      'People should not do things that are disgusting, even if no one is harmed.':
        maxP2,
      'It is better to do good than to do bad.':
        questionnaireParts[1].options[5],
      'One of the worst things a person could do is hurt a defenseless animal.':
        minP2,
      'Justice is the most important requirement for a society.': maxP2,
      'People should be loyal to their family members, even when they have done something wrong.':
        maxP2,
      'Men and women each have different roles to play in society.': maxP2,
      'I would call some acts wrong on the grounds that they are unnatural.':
        maxP2,
    });

    expect(scores).toEqual({
      careHarm: 0,
      fairnessCheating: 1,
      loyaltyBetrayal: 1,
      authoritySubversion: 1,
      sanctityDegradation: 1,
      mathCheck: 0.25,
      goodCheck: 0.25,
    });
  });

  it('should calculate the moral foundations scores 2', () => {
    const scores = getMfq20Scores({
      'Whether or not someone suffered emotionally.': 'Slightly relevant',
      'Whether or not some people were treated differently than others.':
        'Not at all relevant',
      'Whether or not someone’s action showed love for his or her country':
        'Very relevant',
      'Whether or not someone showed a lack of respect for authority.':
        'Extremely relevant',
      'Whether or not someone violated standards of purity and decency.':
        'Somewhat relevant',
      'Whether or not someone was good at math.': 'Not at all relevant',
      'Whether or not someone cared for someone weak or vulnerable':
        'Somewhat relevant',
      'Whether or not someone acted unfairly': 'Extremely relevant',
      'Whether or not someone did something to betray his or her group':
        'Not at all relevant',
      'Whether or not someone conformed to the traditions of society':
        'Extremely relevant',
      'Whether or not someone did something disgusting': 'Not at all relevant',
      'Compassion for those who are suffering is the most crucial virtue.':
        'Strongly agree',
      'When the government makes laws, the number one principle should be ensuring the good of the people.':
        'Strongly disagree',
      'I am proud of my country’s history.': 'Moderately disagree',
      'Respect for authority is something all children need to learn.':
        'Moderately agree',
      'People should not do things that are disgusting, even if no one is harmed.':
        'Strongly agree',
      'It is better to do good than to do bad.': 'Strongly disagree',
      'One of the worst things a person could do is hurt a defenseless animal.':
        'Strongly agree',
      'Justice is the most important requirement for a society.':
        'Moderately disagree',
      'People should be loyal to their family members, even when they have done something wrong.':
        'Slightly agree',
      'Men and women each have different roles to play in society.':
        'Strongly agree',
      'I would call some acts wrong on the grounds that they are unnatural.':
        'Strongly disagree',
    });

    expect(scores).toEqual({
      authoritySubversion: 0.95,
      careHarm: 0.75,
      fairnessCheating: 0.3,
      goodCheck: 0,
      loyaltyBetrayal: 0.4,
      mathCheck: 0,
      sanctityDegradation: 0.4,
    });
  });
});
