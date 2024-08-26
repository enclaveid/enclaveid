import { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

export default {
  title: 'Components/Button',
  component: Button,
  argTypes: {
    label: {
      control: 'text',
      defaultValue: 'Default Button',
    },
    variant: {
      control: {
        type: 'select',
        options: ['primary', 'secondary', 'tertiary'],
      },
      defaultValue: 'primary',
    },
    fullWidth: {
      control: 'boolean',
      defaultValue: false,
    },
  },
} as Meta;

export const Primary: StoryObj<typeof Button> = {
  args: {
    label: 'Primary Button',
    variant: 'primary',
    fullWidth: false,
  },
};

export const Secondary: StoryObj<typeof Button> = {
  args: {
    label: 'Secondary Button',
    variant: 'secondary',
    fullWidth: false,
  },
};

export const Tertiary: StoryObj<typeof Button> = {
  args: {
    label: 'Tertiary Button',
    variant: 'tertiary',
    fullWidth: false,
  },
};
