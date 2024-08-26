import { Meta, StoryObj } from '@storybook/react';
import { LoginForm, LoginFormProps } from './LoginForm';
import { withRouter } from 'storybook-addon-remix-react-router';
export default {
  title: 'Components/Auth/LoginForm',
  component: LoginForm,
  decorators: [withRouter],
} as Meta;

export const Default: StoryObj<LoginFormProps> = {
  args: {
    handleSubmit: function (email, password) {
      console.log(`Email: ${email}, Password: ${password}`);
    },
  },
  render: function (args) {
    return <LoginForm {...args} />;
  },
};
