import { Meta, StoryObj } from '@storybook/react';
import * as icons from './Icons';

const meta: Meta<typeof IconsStory> = {
  title: 'Components/Icons',
  component: IconsStory,
};

export default meta;

function IconsStory() {
  return (
    <div>
      {Object.entries(icons).map(([name, Icon]) => (
        <div
          key={name}
          style={{ display: 'flex', alignItems: 'center', padding: '10px' }}
        >
          <span style={{ marginRight: 8 }}>{name}</span>
          <Icon />
        </div>
      ))}
    </div>
  );
}

export const Icons: StoryObj<typeof IconsStory> = {};
