import classNames from 'classnames';
import { Outlet, useLocation } from 'react-router-dom';
import { Tab } from './Tab';

type TabsProps = {
  tabs: {
    title: string;
    path: string;
  }[];
};

function Tabs({ tabs }: TabsProps) {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);
  const showTabs = pathSegments.length <= 3;

  return (
    <div className="sm:px-6 px-0">
      {showTabs && !pathSegments.includes('account-settings') && (
        <div className="flex overflow-auto border-b border-[#E5E8EE] hideScrollbar pb-1">
          {tabs.map((tab, index) => (
            <Tab {...tab} key={index} />
          ))}
        </div>
      )}
      <div className={classNames(showTabs ? '' : 'lg:mt-[46px] mt-8')}>
        <Outlet />
      </div>
    </div>
  );
}

export { Tabs };
