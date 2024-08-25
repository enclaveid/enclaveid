import { Meta, StoryObj } from '@storybook/react';
import { CreateProfileForm } from './CreateProfileForm';
import { withRouter } from 'storybook-addon-remix-react-router';

export default {
  title: 'Components/CreateProfileForm',
  component: CreateProfileForm,
  argTypes: {},
  decorators: [withRouter],
} as Meta;

export const Default: StoryObj<typeof CreateProfileForm> = {
  args: {},
};
