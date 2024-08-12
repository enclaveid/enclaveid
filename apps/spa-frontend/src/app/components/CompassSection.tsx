import { useState } from 'react';
import CompassChart from './CompassChart';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { useNavigate } from 'react-router-dom';
import { compassChartData } from './mock-data';
import { CustomDrawer } from './CustomDrawer';

function CompassSection() {
  const navigate = useNavigate();
  const { setLink } = useBreadcrumb();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleClick = () => {
    const screenWidth = window.innerWidth;
    if (screenWidth > 640) {
      setLink('Compass');
      navigate(`/dashboard/politics/compass`, {
        state: { compassChartData },
      });
    } else {
      setIsDrawerOpen(true);
    }
  };

  return (
    <>
      <div className="flex flex-col gap-2.5 items-center">
        <h2 className="chart-title">Compass</h2>

        <CompassChart {...compassChartData} handleClick={handleClick} />
      </div>
      <CustomDrawer
        title={'Compass'}
        isOpen={isDrawerOpen}
        setIsDrawerOpen={setIsDrawerOpen}
      >
        <div className="flex flex-col gap-7">
          {/* <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
            Your Results
          </h2> */}
          <div className="gap-9 flex flex-col overflow-y-auto">
            <CompassChart
              {...compassChartData}
              showDescription={true}
              handleClick={handleClick}
            />
            <div className="mt-3 mb-8">
              {/* <SimilarProfileBadge peopleCount={253} /> */}
            </div>
          </div>
        </div>
      </CustomDrawer>
    </>
  );
}

export { CompassSection };
