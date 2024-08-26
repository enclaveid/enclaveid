import { Meta, StoryObj } from '@storybook/react';
import { LifeJourneys } from './LifeJourneys';

export default {
  title: 'Components/LifeJourneys',
  component: LifeJourneys,
  argTypes: {},
} as Meta;

export const Default: StoryObj<typeof LifeJourneys> = {
  args: {},
};
