import { Meta, StoryObj } from '@storybook/react';
import { StepForm } from './StepForm';
import { withRouter } from 'storybook-addon-remix-react-router';
import { questionnaires } from '@enclaveid/shared';

export default {
  title: 'Components/StepForm',
  component: StepForm,
  decorators: [withRouter],
  render: (args) => <StepForm {...args} />,
} as Meta;

export const Default: StoryObj = {
  args: {
    questionnaire: questionnaires[1],
  },
};
