import { Outlet } from 'react-router-dom';
import { CommonLayout } from './CommonLayout';

function LifeJourneyLayout() {
  return (
    <CommonLayout>
      <Outlet />
    </CommonLayout>
  );
}

export { LifeJourneyLayout };
