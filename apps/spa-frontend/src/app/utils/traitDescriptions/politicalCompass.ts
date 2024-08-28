import {
  PoliticalCompassPartial,
  politicalCompassToString,
} from '@enclaveid/shared';

const compassDescriptions = {
  'Authoritarian Center':
    "You believe in a strong, centralized government that balances both left and right economic policies. While you support some personal freedoms, you think a powerful state is necessary to maintain order and implement effective policies. You're open to government intervention in both economic and social spheres when you believe it serves the greater good.",
  'Libertarian Center':
    'You value personal freedom highly and are skeptical of excessive government power, but you also see a role for moderate state intervention. Economically, you believe in a mixed system that incorporates both free market principles and some social safety nets. You strive for a balance between individual liberty and community well-being.',
  'Authoritarian Right':
    'You emphasize traditional social values, a strong national identity, and a hierarchical society. While you support free market economics, you believe in significant state involvement to maintain order and tradition.',
  'Authoritarian Left':
    'You advocate for a strong state to ensure economic equality and robust social programs. You prioritize collective needs over individual rights, believing that a powerful government can best serve the common good.',
  'Libertarian Right':
    'You champion free market capitalism and minimal government intervention in both economic and social affairs. Individual liberty and property rights are your top priorities, and you believe people should be free to make their own choices without state interference.',
  'Libertarian Left':
    'You support personal freedoms and social equality, while advocating for cooperative economics and decentralized political structures. You believe in community-based solutions and are skeptical of both big government and big business.',
};

export function getPoliticalCompassTraitDescription(
  data: PoliticalCompassPartial,
) {
  const label = politicalCompassToString(data);

  return compassDescriptions[label];
}
