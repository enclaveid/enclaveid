import * as React from 'react';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
} from './sidebar';

import { Logo } from './logo';
import {
  CodeIcon,
  PersonIcon,
  HomeIcon,
  Share1Icon,
} from '@radix-ui/react-icons'; // This is sample data.
const data = {
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

export function AppSidebar({
  LogoutButton,
  ...props
}: React.ComponentProps<typeof Sidebar> & { LogoutButton: React.ReactNode }) {
  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2">
          <Logo />
          <p className="text-lg font-bold">EnclaveID</p>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {data.navMain.map((item) => (
          <SidebarGroup key={item.title}>
            <SidebarGroupLabel>{item.title}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {item.items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild isActive={item.isActive}>
                      <a href={item.url}>
                        {item.icon}
                        {item.title}
                      </a>
                    </SidebarMenuButton>
                    {item.badge && (
                      <SidebarMenuBadge className="bg-primary text-primary-foreground">
                        {item.badge}
                      </SidebarMenuBadge>
                    )}
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter>{LogoutButton}</SidebarFooter>
    </Sidebar>
  );
}
