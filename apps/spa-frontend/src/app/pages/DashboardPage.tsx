import { Tabs } from '../components/Tabs';

const tabs = [
  { title: 'Personality', path: '/dashboard/traits/personality' },
  { title: 'Politics', path: '/dashboard/traits/politics' },
  { title: 'Career', path: '/dashboard/traits/career' },
];

function DashboardPage() {
  return <Tabs tabs={tabs} />;
}

export { DashboardPage };
