import { Breadcrumb } from '../components/Breadcrumb';

import { Sidebar } from '../components/Sidebar';
import { Tabs } from '../components/Tabs';
import { SidebarContainer } from '../components/containers/SidebarContainer';
import { RequireAuth } from '../providers/AuthProvider';

const tabs = [
  { title: 'Personality', path: '/dashboard/personality' },
  { title: 'Politics', path: '/dashboard/politics' },
  { title: 'Career', path: '/dashboard/career' },
];

function DashboardPage() {
  return (
    <RequireAuth>
      <div className="h-screen bg-white flex sm:flex-row flex-col">
        <SidebarContainer>
          <Sidebar />
        </SidebarContainer>
        <div className="flex flex-1 flex-col overflow-y-auto">
          <div className="pt-[54px] pb-4 sm:block hidden px-6">
            <Breadcrumb />
          </div>
          <Tabs tabs={tabs} />
        </div>
      </div>
    </RequireAuth>
  );
}

export { DashboardPage };
