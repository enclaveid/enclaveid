const bigFiveTraitDescriptions = {
  openness: {
    low: `Low openness to experience is associated with a preference for routine and tradition, and a dislike for change and new experiences.`,
    neutral: `Average openness to experience is associated with a moderate preference for variety and change, and a moderate love for new experiences and ideas.`,
    high: `High openness to experience is associated with a preference for variety and change, and a love for new experiences and ideas.`,
  },
  conscientiousness: {
    low: `Low conscientiousness is associated with a preference for spontaneity and flexibility, and a dislike for structure and routine.`,
    neutral: `Average conscientiousness is associated with a moderate preference for structure and routine, and a moderate dislike for spontaneity and flexibility.`,
    high: `High conscientiousness is associated with a preference for structure and routine, and a love for order and organization.`,
  },
  extraversion: {
    low: `Low extraversion is associated with a preference for solitude and introspection, and a dislike for social interaction.`,
    neutral: `Average extraversion is associated with a moderate preference for social interaction, and a moderate dislike for solitude and introspection.`,
    high: `High extraversion is associated with a preference for social interaction, and a love for variety and change.`,
  },
  agreeableness: {
    low: `Low agreeableness is associated with a preference for assertiveness and dominance, and a dislike for cooperation and compromise.`,
    neutral: `Average agreeableness is associated with a moderate preference for cooperation and compromise, and a moderate dislike for assertiveness and dominance.`,
    high: `High agreeableness is associated with a preference for cooperation and compromise, and a love for harmony and cooperation.`,
  },
  neuroticism: {
    low: `Low neuroticism is associated with a preference for stability and security, and a dislike for change and uncertainty.`,
    neutral: `Average neuroticism is associated with a moderate preference for stability and security, and a moderate dislike for change and uncertainty.`,
    high: `High neuroticism is associated with a preference for change and uncertainty, and a love for variety and change.`,
  },
};

export function getBigFiveTraitDescription(trait: string, value: number) {
  if (value > 0.6) {
    return bigFiveTraitDescriptions[trait].high;
  } else if (value < 0.4) {
    return bigFiveTraitDescriptions[trait].low;
  } else {
    return bigFiveTraitDescriptions[trait].neutral;
  }
}
