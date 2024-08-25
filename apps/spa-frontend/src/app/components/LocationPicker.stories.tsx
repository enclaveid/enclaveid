import { Meta, StoryObj } from '@storybook/react';
import { LocationPicker } from './LocationPicker';

export default {
  title: 'Components/LocationPicker',
  component: LocationPicker,
} as Meta;

export const Default: StoryObj<typeof LocationPicker> = {
  args: {},
};
