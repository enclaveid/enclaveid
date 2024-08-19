import { Meta, StoryObj } from '@storybook/react';
import { CreateProfileForm } from './CreateProfileForm';

export default {
  title: 'Components/CreateProfileForm',
  component: CreateProfileForm,
  argTypes: {},
} as Meta;

export const Default: StoryObj<typeof CreateProfileForm> = {
  args: {},
};
