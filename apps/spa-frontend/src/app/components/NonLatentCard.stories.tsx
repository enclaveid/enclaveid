import { Meta, StoryObj } from '@storybook/react';
import { NonLatentCard } from './NonLatentCard';
import { LotsOfData } from './TinyBarChart.stories';

export default {
  title: 'Components/NonLatentCard',
  component: NonLatentCard,
} as Meta<typeof NonLatentCard>;

export const Default: StoryObj<typeof NonLatentCard> = {
  args: {
    title: 'Title',
    description: 'Description',
    isViewed: false,
  },
};

export const Selected: StoryObj<typeof NonLatentCard> = {
  args: {
    title: 'Title',
    description: 'Description',
    isViewed: true,
  },
};

export const WithChart: StoryObj<typeof NonLatentCard> = {
  args: {
    title: 'Some kind of title used for placeholder',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed etiam, ut inchoavit aut inchoare potuit, dissimilem et sui dissimilem esse potest, dissimilem sui dissimilem esse potest.',
    isViewed: false,
    activityDates: LotsOfData.args.dates,
  },
};

export const WithSimilarity: StoryObj<typeof NonLatentCard> = {
  args: {
    title: 'Some kind of title used for placeholder',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed etiam, ut inchoavit aut inchoare potuit, dissimilem et sui dissimilem esse potest, dissimilem sui dissimilem esse potest.',
    isViewed: false,
    similarityPercentage: 80,
  },
};
