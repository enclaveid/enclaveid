import { Outlet } from 'react-router-dom';
import { CommonLayout } from './CommonLayout';

export function AccountSettingsLayout() {
  return (
    <CommonLayout>
      <Outlet />
    </CommonLayout>
  );
}
