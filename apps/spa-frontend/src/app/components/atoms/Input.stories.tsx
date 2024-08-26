import { Meta, StoryObj } from '@storybook/react';
import { Input } from './Input';

const meta: Meta<typeof Input> = {
  title: 'Components/Input',
  component: Input,
  argTypes: {
    label: {
      control: 'text',
      defaultValue: 'Email Address',
    },
    id: {
      control: 'text',
    },
    placeholder: {
      control: 'text',
      defaultValue: 'user@example.com',
    },
    fullWidth: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

export default meta;

type Story = StoryObj<typeof Input>;

export const Default: Story = {
  args: {
    label: 'Email Address',
    id: 'email',
    placeholder: 'user@example.com',
    fullWidth: false,
  },
};

export const Password: Story = {
  args: {
    ...Default.args,
    label: 'Password',
    id: 'password',
    placeholder: '**********',
  },
};
