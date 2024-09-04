import { Meta, StoryObj } from '@storybook/react';
import { MFTChart } from './MFTChart';
import { MFTChartData } from '../utils/mock-data';

export default {
  title: 'Components/MFTChart',
  component: MFTChart,
  argTypes: {
    harm: {
      control: 'number',
      defaultValue: MFTChartData.harm,
      description: 'Harm value (0 to 1 scale)',
    },
    fairness: {
      control: 'number',
      defaultValue: MFTChartData.fairness,
      description: 'Fairness value (0 to 1 scale)',
    },
    authority: {
      control: 'number',
      defaultValue: MFTChartData.authority,
      description: 'Authority value (0 to 1 scale)',
    },
    ingroup: {
      control: 'number',
      defaultValue: MFTChartData.ingroup,
      description: 'Ingroup value (0 to 1 scale)',
    },
    purity: {
      control: 'number',
      defaultValue: MFTChartData.purity,
      description: 'Purity value (0 to 1 scale)',
    },
    mftChartAvailable: {
      control: 'boolean',
      defaultValue: true,
      description: 'Toggles the availability state of the MFT chart',
    },
    loading: {
      control: 'boolean',
      defaultValue: false,
      description: 'Displays a loading skeleton',
    },
    error: {
      control: 'boolean',
      defaultValue: false,
      description: 'Displays an error state',
    },
  },
} as Meta<typeof MFTChart>;

const { description, ...circles } = MFTChartData;

export const Default: StoryObj<typeof MFTChart> = {
  args: circles,
  decorators: [
    (Story) => (
      <div style={{ margin: '20px', position: 'relative', maxWidth: '536px' }}>
        <Story />
      </div>
    ),
  ],
};

export const Loading: StoryObj<typeof MFTChart> = {
  args: {
    ...circles,
    loading: true,
  },
  decorators: [
    (Story) => (
      <div style={{ margin: '20px', position: 'relative', maxWidth: '536px' }}>
        <Story />
      </div>
    ),
  ],
};

export const Error: StoryObj<typeof MFTChart> = {
  args: {
    ...circles,
    error: true,
  },
  decorators: [
    (Story) => (
      <div style={{ margin: '20px', position: 'relative', maxWidth: '536px' }}>
        <Story />
      </div>
    ),
  ],
};

export const Unavailable: StoryObj<typeof MFTChart> = {
  args: {
    ...circles,
    mftChartAvailable: false,
  },
  decorators: [
    (Story) => (
      <div style={{ margin: '20px', position: 'relative', maxWidth: '536px' }}>
        <Story />
      </div>
    ),
  ],
};
