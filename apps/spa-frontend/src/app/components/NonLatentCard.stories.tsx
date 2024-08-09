import { Meta, StoryObj } from '@storybook/react';
import { NonLatentCard } from './NonLatentCard';

export default {
  title: 'Components/NonLatentCard',
  component: NonLatentCard,
} as Meta<typeof NonLatentCard>;

export const Default: StoryObj<typeof NonLatentCard> = {
  args: {
    title: 'Title',
    description: 'Description',
    isSelected: false,
  },
};

export const Selected: StoryObj<typeof NonLatentCard> = {
  args: {
    title: 'Title',
    description: 'Description',
    isSelected: true,
  },
};
