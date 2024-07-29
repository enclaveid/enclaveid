import { Outlet } from 'react-router-dom';
import { CommonLayout } from './CommonLayout';

function SocialLayout() {
  return (
    <CommonLayout>
      <Outlet />
    </CommonLayout>
  );
}

export { SocialLayout };
