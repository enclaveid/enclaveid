import { MoralFoundationsPartial } from '@enclaveid/shared';

const mftDescriptions = {
  careHarm: {
    name: 'Harm (Care)',
    low: "You tend to prioritize other values over care and empathy in your moral reasoning. While you're not indifferent to others' suffering, you might place less emphasis on it when making decisions. You may believe that too much focus on care can lead to overprotectiveness or inefficiency in solving larger problems.",
    high: "You have a strong emphasis on kindness, nurturing, and protecting others from harm. You're likely to be deeply affected by others' pain and suffering, and you often go out of your way to help those in need. You value compassion highly and may be drawn to caregiving roles or professions.",
  },
  fairnessCheating: {
    name: 'Fairness (Cheating)',
    low: "You tend to place less emphasis on equality and proportional fairness in your moral reasoning. While you don't necessarily endorse injustice, you might be more accepting of certain inequalities as natural or even beneficial for society. You may prioritize other values, such as tradition or efficiency, over strict fairness.",
    high: "You have a strong belief in justice, equality, and proportionality. You're likely to be sensitive to issues of fairness and may become upset when you perceive people aren't getting what they deserve (good or bad). You probably support systems that ensure equal opportunities and may advocate for marginalized groups.",
  },
  loyaltyBetrayal: {
    name: 'Ingroup (Betrayal)',
    low: "You tend to be more individualistic and may not feel strong ties to groups or communities. You're likely to prioritize personal principles over group loyalty and might be comfortable changing allegiances if it aligns with your personal beliefs or benefits. You may view excessive group loyalty as tribalism.",
    high: "You value strong in-group loyalty, patriotism, and self-sacrifice for the group. You're likely to feel deep connections to your communities, whether they're family, friends, or larger entities like your country. You might view loyalty as a key virtue and feel particularly hurt by perceived betrayal.",
  },
  authoritySubversion: {
    name: 'Authority (Subversion)',
    low: "You tend to reject hierarchy and may have anti-authoritarian leanings. You're likely to question traditional power structures and may be skeptical of those in positions of authority. You might value flat organizational structures and believe that respect should be earned, not automatically granted based on position.",
    high: "You have a strong respect for tradition and legitimate authority, valuing order and stability. You're likely to believe in the importance of social hierarchies and may feel that challenging established systems can lead to chaos. You might prioritize duty, obedience, and respect for elders or those in positions of authority.",
  },
  sanctityDegradation: {
    name: 'Purity (Degradation)',
    low: "You're likely to reject the idea that anything is inherently sacred or pure. You probably have a more materialistic worldview and may be skeptical of spiritual or religious concepts. You might be more comfortable with things others find 'unclean' or 'profane' and could view such distinctions as arbitrary.",
    high: "You have a strong sense of purity and strive to avoid contamination, both physical and spiritual. You're likely to believe in the sanctity of certain objects, places, or concepts. You might have strong reactions to perceived violations of purity and may engage in purification rituals or practices. You could view certain things as inherently sacred or untouchable.",
  },
  libertyOppression: {
    name: 'Liberty-Oppression',
    low: "You're more accepting of external control and might be comfortable with authoritarian systems. You may believe that strong central control is necessary for a functioning society and could be willing to trade some personal freedoms for security or efficiency. You might be less likely to rebel against restrictions on individual liberty.",
    high: "You place a strong emphasis on individual freedom and resist what you perceive as tyranny. You're likely to be highly sensitive to infringements on personal liberty and may react strongly against attempts to control or coerce. You probably value autonomy highly and might be drawn to libertarian ideals or movements that champion individual rights.",
  },
};

export function getMoralFoundationsTraitDescription(
  mft: MoralFoundationsPartial,
) {
  return Object.entries(mft)
    .map(([key, value]) => {
      const v = value > 0.5 ? 'high' : 'low';
      return `**${mftDescriptions[key].name}**: ${mftDescriptions[key][v]} \n\n`;
    })
    .join('');
}
