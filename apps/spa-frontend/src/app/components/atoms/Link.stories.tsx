import { Meta, StoryObj } from '@storybook/react';
import { Link } from './Link';

export default {
  title: 'Components/Link',
  component: Link,
  argTypes: {
    href: { control: 'text' },
    target: { control: 'text' },
    children: { control: 'text', defaultValue: 'Click Me' },
    underlined: { control: 'boolean', defaultValue: true },
  },
} as Meta;

export const Default: StoryObj<typeof Link> = {
  args: {
    href: 'https://example.com',
    target: '_blank',
    children: 'Example Link',
    underlined: true,
  },
};
