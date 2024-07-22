import { CommonLayout } from '../components/CommonLayout';

import { Tabs } from '../components/Tabs';
import { RequireAuth } from '../providers/AuthProvider';

const tabs = [
  { title: 'Personality', path: '/dashboard/personality' },
  { title: 'Politics', path: '/dashboard/politics' },
  { title: 'Career', path: '/dashboard/career' },
];

function DashboardPage() {
  return (
    <RequireAuth>
      <CommonLayout>
        <Tabs tabs={tabs} />
      </CommonLayout>
    </RequireAuth>
  );
}

export { DashboardPage };
