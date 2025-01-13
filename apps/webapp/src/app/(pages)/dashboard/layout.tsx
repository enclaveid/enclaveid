// layout.tsx
import { AppSidebar } from '@enclaveid/ui/app-sidebar';
import { Separator } from '@enclaveid/ui/separator';
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@enclaveid/ui/sidebar';
import { LogoutButton } from '../../components/logout-button';
import { DashboardBreadcrumb } from '../../components/dashboard-breadcrumb';
import {
  CodeIcon,
  HomeIcon,
  Share1Icon,
  PersonIcon,
} from '@radix-ui/react-icons';

const sidebarItems = {
  navMain: [
    {
      title: 'Dashboard',
      items: [
        {
          title: 'Home',
          url: '/dashboard/home',
          icon: <HomeIcon />,
        },
        {
          title: 'Social',
          url: '#',
          icon: <Share1Icon />,
          badge: 'Coming soon!',
        },
      ],
    },
    {
      title: 'Settings',
      items: [
        {
          title: 'API Keys',
          url: '/dashboard/api-keys',
          icon: <CodeIcon />,
        },
        {
          title: 'Profile',
          url: '/dashboard/profile',
          icon: <PersonIcon />,
        },
      ],
    },
  ],
};

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar LogoutButton={<LogoutButton />} sidebarItems={sidebarItems} />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <DashboardBreadcrumb />
        </header>
        <div className="flex flex-1 flex-col gap-4 p-4">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
