import { Meta, StoryObj } from '@storybook/react';
import { BigFiveCard } from './BigFiveCard';
import { bigFiveCard } from '../utils/mock-data';
import { withRouter } from 'storybook-addon-remix-react-router';
import { BreadcrumbProvider } from '../providers/BreadcrumbContext';

export default {
  title: 'Components/BigFiveCard',
  component: BigFiveCard,
  decorators: [withRouter],
  argTypes: {
    title: {
      control: 'text',
      defaultValue: 'Personality Traits',
    },
  },
} as Meta<typeof BigFiveCard>;

export const Default: StoryObj<typeof BigFiveCard> = {
  args: {
    title: bigFiveCard.title,
    data: bigFiveCard.data,
  },
  decorators: [
    (Story) => (
      <div style={{ maxWidth: '538px' }}>
        <BreadcrumbProvider>
          <Story />
        </BreadcrumbProvider>
      </div>
    ),
  ],
};
