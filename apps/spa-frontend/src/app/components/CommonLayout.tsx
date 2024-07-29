import { ReactNode } from 'react';
import { SidebarContainer } from './containers/SidebarContainer';
import { Sidebar } from './Sidebar';
import { Breadcrumb } from './Breadcrumb';

function CommonLayout({ children }: { children: ReactNode }) {
  return (
    <div className="h-screen bg-white flex sm:flex-row flex-col">
      <SidebarContainer>
        <Sidebar />
      </SidebarContainer>
      <div className="flex flex-1 flex-col overflow-y-auto">
        <div className="pt-[54px] pb-4 sm:block hidden px-6">
          <Breadcrumb />
        </div>
        {children}
      </div>
    </div>
  );
}

export { CommonLayout };
