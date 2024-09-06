import { useState } from 'react';
import CompassChart from './CompassChart';
import { useNavigate } from 'react-router-dom';
import { compassChartData } from '../utils/mock-data';
import { CustomDrawer } from './CustomDrawer';
import { DynamicAreaLoading } from './DynamicAreaLoading';
import { UnavailableChartOverlay } from './UnavailableChartOverlay';

const mockData = compassChartData;

export interface CompassSectionProps {
  isLoading?: boolean;
  data?: typeof compassChartData;
}

export function CompassSection({
  isLoading,
  data = mockData,
}: CompassSectionProps) {
  const navigate = useNavigate();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleClick = () => {
    const screenWidth = window.innerWidth;
    if (screenWidth > 640) {
      navigate(`compass`, {
        state: { compassChartData: data },
      });
    } else {
      setIsDrawerOpen(true);
    }
  };

  return (
    <>
      <div className="flex flex-col gap-2.5 items-center">
        <h2 className="chart-title">Political Compass</h2>
        {isLoading ? (
          <DynamicAreaLoading />
        ) : (
          <UnavailableChartOverlay
            enabled={data === mockData}
            questionnaireStatusKey="isMoralFoundationsComplete"
          >
            <CompassChart {...data} handleClick={handleClick} />
          </UnavailableChartOverlay>
        )}
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
              x={data.x}
              y={data.y}
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
