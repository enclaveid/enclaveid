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

export function AppSidebar({
  LogoutButton,
  sidebarItems,
  ...props
}: React.ComponentProps<typeof Sidebar> & {
  LogoutButton: React.ReactNode;
  sidebarItems: {
    navMain: {
      title: string;
      items: {
        title: string;
        url: string;
        icon: React.ReactNode;
        isActive?: boolean;
        badge?: React.ReactNode;
      }[];
    }[];
  };
}) {
  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2">
          <Logo />
          <p className="text-lg font-bold">EnclaveID</p>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {sidebarItems.navMain.map((item) => (
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
