import { Meta, StoryObj } from '@storybook/react';
import { InfiniteCardLoader } from './InfiniteCardLoader';

export default {
  title: 'Components/InfiniteCardLoader',
  component: InfiniteCardLoader,
} as Meta;

export const Default: StoryObj<typeof InfiniteCardLoader> = {
  args: {},
};
