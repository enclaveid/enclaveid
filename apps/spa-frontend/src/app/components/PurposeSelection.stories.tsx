import { Meta, StoryObj } from '@storybook/react';
import { PurposeSelection } from './PurposeSelection';

export default {
  title: 'Components/PurposeSelection',
  component: PurposeSelection,
  argTypes: {},
} as Meta;

export const Default: StoryObj<typeof PurposeSelection> = {
  args: {},
};
