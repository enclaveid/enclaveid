import { Meta, StoryObj } from '@storybook/react';
import { SocialCard } from './SocialCard';
import { withRouter } from 'storybook-addon-remix-react-router';
import { Gender } from '@prisma/client';

export default {
  title: 'Components/SocialCard',
  component: SocialCard,
  decorators: [withRouter],
} as Meta;

export const Default: StoryObj<typeof SocialCard> = {
  decorators: [
    (Story) => (
      <div style={{ maxWidth: '538px' }}>
        <Story />
      </div>
    ),
  ],
  args: {
    userMatchOverview: {
      displayName: 'John Doe',
      gender: Gender.Male,
      country: 'Indonesia',
      overallSimilarity: 0.8,
      usersOverallSimilarityId: '1',
    },
    loading: false,
  },
};

export const Loading: StoryObj<typeof SocialCard> = {
  decorators: [
    (Story) => (
      <div style={{ maxWidth: '538px' }}>
        <Story />
      </div>
    ),
  ],
  args: {
    loading: true,
  },
};
