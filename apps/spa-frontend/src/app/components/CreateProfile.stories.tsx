import { Meta, StoryObj } from '@storybook/react';
import { CreateProfile } from './CreateProfile';

export default {
  title: 'Components/CreateProfile',
  component: CreateProfile,
  argTypes: {},
} as Meta;

export const Default: StoryObj<typeof CreateProfile> = {
  args: {},
};
