'use client';

import { ExitIcon } from '@radix-ui/react-icons';

import { SidebarMenuButton } from '@enclaveid/ui/sidebar';
import { logOut } from '../actions/auth/logOut';

export function LogoutButton() {
  return (
    <SidebarMenuButton
      onClick={() => {
        logOut();
      }}
    >
      <ExitIcon />
      Logout
    </SidebarMenuButton>
  );
}
