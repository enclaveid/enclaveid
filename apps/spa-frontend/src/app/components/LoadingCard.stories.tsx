import { Meta, StoryObj } from '@storybook/react';
import { LoadingCard } from './LoadingCard';

export default {
  title: 'Components/LoadingCard',
  component: LoadingCard,
} as Meta;

export const Default: StoryObj<typeof LoadingCard> = {
  args: {},
};
