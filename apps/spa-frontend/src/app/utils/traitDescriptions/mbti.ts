import { MbtiPartial, mbtiToString } from '@enclaveid/shared';

const shortDescriptions = {
  ISTJ: 'Quiet, serious, earn success by thoroughness and dependability. Practical, matter-of-fact, realistic, and responsible.',
  ISFJ: 'Quiet, friendly, responsible, and conscientious. Committed and steady in meeting obligations. Thorough, painstaking, and accurate.',
  INFJ: 'Seek meaning and connection in ideas, relationships, and material possessions. Want to understand what motivates people and are insightful about others.',
  INTJ: 'Have original minds and great drive for implementing their ideas and achieving their goals. Quickly see patterns in external events and develop long-range explanatory perspectives.',
  ISTP: 'Tolerant and flexible, quiet observers until a problem appears, then act quickly to find workable solutions. Analyze what makes things work and readily get through large amounts of data to isolate the core of practical problems.',
  ISFP: "Quiet, friendly, sensitive, and kind. Enjoy the present moment, what's going on around them. Like to have their own space and to work within their own time frame. Loyal and committed to their values and to people who are important to them.",
  INFP: 'Idealistic, loyal to their values and to people who are important to them. Want an external life that is congruent with their values. Curious, quick to see possibilities, can be catalysts for implementing ideas.',
  INTP: 'Seek to develop logical explanations for everything that interests them. Theoretical and abstract, interested more in ideas than in social interaction. Quiet, contained, flexible, and adaptable.',
  ESTP: 'Flexible and tolerant, they take a pragmatic approach focused on immediate results. Theories and conceptual explanations bore them - they want to act energetically to solve the problem.',
  ESFP: 'Outgoing, friendly, and accepting. Exuberant lovers of life, people, and material comforts. Enjoy working with others to make things happen. Bring common sense and a realistic approach to their work, and make work fun.',
  ENFP: 'Warmly enthusiastic and imaginative. See life as full of possibilities. Make connections between events and information very quickly, and confidently proceed based on the patterns they see.',
  ENTP: 'Quick, ingenious, stimulating, alert, and outspoken. Resourceful in solving new and challenging problems. Adept at generating conceptual possibilities and then analyzing them strategically.',
  ESTJ: 'Practical, realistic, matter-of-fact. Decisive, quickly move to implement decisions. Organize projects and people to get things done, focus on getting results in the most efficient way possible.',
  ESFJ: 'Warmhearted, conscientious, and cooperative. Want harmony in their environment, work with determination to establish it. Like to work with others to complete tasks accurately and on time.',
  ENFJ: 'Warm, empathetic, responsive, and responsible. Highly attuned to the emotions, needs, and motivations of others. Find potential in everyone, want to help others fulfill their potential.',
  ENTJ: 'Frank, decisive, assume leadership readily. Quickly see illogical and inefficient procedures and policies, develop and implement comprehensive systems to solve organizational problems.',
};

const mbtiLetters = {
  E: {
    name: 'Extraversion',
    description:
      'Extraverts are energized by social interaction and tend to be more outgoing and talkative. They prefer to think out loud and enjoy a wide circle of friends and acquaintances. Extraverts are action-oriented and tend to make quick decisions. They are often seen as approachable and enthusiastic.',
  },
  I: {
    name: 'Introversion',
    description:
      'Introverts are energized by spending time alone and tend to be more reserved and thoughtful. They prefer deep, one-on-one conversations and usually have a small circle of close friends. Introverts process information internally before acting and may need time to recharge after social interactions. They are often perceived as calm and reflective.',
  },
  S: {
    name: 'Sensing',
    description:
      'Sensing individuals focus on concrete facts and details. They trust information that comes directly from their five senses and prefer practical, realistic approaches. Sensors live in the present, value past experiences, and tend to be detail-oriented. They often excel at tasks requiring precision and careful observation.',
  },
  N: {
    name: 'Intuition',
    description:
      'Intuitive individuals focus on the big picture and abstract concepts. They trust their hunches and look for patterns and connections between facts. Intuitives are often future-oriented, imaginative, and enjoy exploring possibilities. They tend to be innovative and may prefer novelty over routine.',
  },
  T: {
    name: 'Thinking',
    description:
      'Thinking types make decisions based on logic, consistency, and objective criteria. They tend to analyze pros and cons and prefer to remain emotionally detached when solving problems. Thinkers value fairness and may appear impersonal or critical at times. They often excel in fields requiring logical analysis and impartial decision-making.',
  },
  F: {
    name: 'Feeling',
    description:
      "Feeling types make decisions based on personal values and how their choices will affect others. They consider the human element in all situations and value harmony and empathy. Feelers are often skilled at understanding others' emotions and motivations. They may excel in fields requiring interpersonal skills and emotional intelligence.",
  },
  J: {
    name: 'Judging',
    description:
      'Judging types prefer structure, order, and closure in their lives. They like to have things settled and tend to be organized and planful. Judgers often create schedules, make lists, and prefer to finish one project before starting another. They may appear decisive and prefer clearly defined goals and deadlines.',
  },
  P: {
    name: 'Perceiving',
    description:
      'Perceiving types prefer flexibility, spontaneity, and keeping their options open. They are adaptable, curious, and often good at improvising. Perceivers tend to be more relaxed about schedules and deadlines, preferring to stay open to new information and last-minute changes. They may appear more casual and open-ended in their approach to life.',
  },
};

function getLongDescription(mbtiString: string) {
  return mbtiString
    .split('')
    .map(
      (letter) =>
        `**${mbtiLetters[letter].name}**: ${mbtiLetters[letter].description} \n\n`,
    )
    .join('');
}

export function getMbtiTraitDescription(mbti: MbtiPartial) {
  const mbtiString = mbtiToString(mbti);

  return {
    shortDescription: shortDescriptions[mbtiString],
    longDescription: getLongDescription(mbtiString),
  };
}
