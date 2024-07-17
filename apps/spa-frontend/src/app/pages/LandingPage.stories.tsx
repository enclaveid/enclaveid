import { Meta, StoryObj } from '@storybook/react/*';
import { LandingPage } from './LandingPage';
import { withRouter } from 'storybook-addon-remix-react-router';

export default {
  title: 'Pages/LandingPage',
  component: LandingPage,
  argTypes: {
    title: {
      control: 'text',
      defaultValue: 'Personality Traits',
    },
  },
  decorators: [withRouter],
} as Meta<typeof LandingPage>;

export const Default: StoryObj = {
  args: {},
};
