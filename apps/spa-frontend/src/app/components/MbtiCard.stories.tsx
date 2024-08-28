import { Meta, StoryObj } from '@storybook/react';
import { MbtiCard } from './MbtiCard';
import { withRouter } from 'storybook-addon-remix-react-router';
import { BreadcrumbProvider } from '../providers/BreadcrumbContext';
import { mbtiCard } from './mock-data';

export default {
  title: 'Components/MbtiCard',
  component: MbtiCard,
  decorators: [withRouter],
} as Meta<typeof MbtiCard>;

export const Default: StoryObj<typeof MbtiCard> = {
  args: {
    header: mbtiCard.header,
    label: mbtiCard.label,
    description: mbtiCard.description,
    data: {
      title: mbtiCard.data.title,
      content: mbtiCard.data.content,
    },
  },
  decorators: [
    (Story) => (
      <BreadcrumbProvider>
        <div style={{ maxWidth: '538px' }}>
          <Story />
        </div>
      </BreadcrumbProvider>
    ),
  ],
};
