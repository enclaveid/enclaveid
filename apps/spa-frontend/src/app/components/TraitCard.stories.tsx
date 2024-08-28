import { Meta, StoryObj } from '@storybook/react';
import { TraitCard } from './TraitCard';
import { bigFiveCard } from './mock-data';

export default {
  title: 'Components/TraitCard',
  component: TraitCard,
  argTypes: {
    value: {
      control: 'range',
      defaultValue: 85,
      min: 0,
      max: 100,
      step: 1,
    },
  },
} as Meta<typeof TraitCard>;

export const Default: StoryObj<typeof TraitCard> = {
  args: {
    label: bigFiveCard.data[0].label,
    value: bigFiveCard.data[0].value,
    description: bigFiveCard.data[0].description,
  },
  decorators: [
    (Story) => (
      <div style={{ maxWidth: '538px' }}>
        <Story />
      </div>
    ),
  ],
};
