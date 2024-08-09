import { StoryFn, Meta } from '@storybook/react';
import { PercentageCircle } from './PercentageCircle';

export default {
  title: 'Components/PercentageCircle',
  component: PercentageCircle,
  argTypes: {
    percentage: {
      control: { type: 'number', min: 0, max: 100 },
    },
    size: {
      control: { type: 'number', min: 0, max: 500 },
    },
  },
} as Meta;

const Template: StoryFn = (args) => (
  <PercentageCircle percentage={args.percentage} size={'lg'} />
);

export const LowPercentage = Template.bind({});
LowPercentage.args = {
  percentage: 25.09384290438,
};

export const MediumPercentage = Template.bind({});
MediumPercentage.args = {
  percentage: 50,
};

export const HighPercentage = Template.bind({});
HighPercentage.args = {
  percentage: 85,
};
