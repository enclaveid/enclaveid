import { Meta, StoryObj } from '@storybook/react';
import { traitCard2 } from '../utils/mock-data';
import { withRouter } from 'storybook-addon-remix-react-router';
import { BreadcrumbProvider } from '../providers/BreadcrumbContext';
import { SixteenPFCard } from './SixteenPFCard';

export default {
  title: 'Components/SixteenPFCard',
  component: SixteenPFCard,
  decorators: [withRouter],
  argTypes: {
    title: {
      control: 'text',
      defaultValue: 'Personality Traits',
    },
  },
} as Meta<typeof SixteenPFCard>;

export const Default: StoryObj<typeof SixteenPFCard> = {
  args: {
    title: '16FP',
    data: traitCard2,
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
