import { Meta, StoryObj } from '@storybook/react/*';
import { LoadingPage } from './LoadingPage';
import { withRouter } from 'storybook-addon-remix-react-router';

export default {
  title: 'Pages/LoadingPage',
  component: LoadingPage,
  argTypes: {
    title: {
      control: 'text',
      defaultValue: 'Personality Traits',
    },
  },
  decorators: [withRouter],
} as Meta<typeof LoadingPage>;

export const Default: StoryObj = {
  args: {},
};
