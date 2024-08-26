import { Meta, StoryObj } from '@storybook/react';
import { SignupForm, SignupFormProps } from './SignupForm';
import { withRouter } from 'storybook-addon-remix-react-router';

export default {
  title: 'Components/Auth/SignupForm',
  component: SignupForm,
  decorators: [withRouter],
} as Meta;

export const Default: StoryObj<SignupFormProps> = {
  args: {
    handleSubmit: function (formData) {
      console.log(formData);
    },
  },
  render: function (args) {
    return <SignupForm {...args} />;
  },
};
