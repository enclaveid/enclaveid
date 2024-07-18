import { useNavigate } from 'react-router-dom';
import { Button } from './Button';

import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { useState } from 'react';
import { radarChart } from './mock-data';
import { SimilarProfileBadge } from './SimilarProfileBadge';
import { RadarChart, RadarChartProps } from './RadarChart';
import { CustomDrawer } from './CustomDrawer';

export const findHighestValues = (props: RadarChartProps): string[] => {
  const highestKeys: string[] = [];
  let highestValue = 0;

  Object.entries(props.values).forEach(([key, value]) => {
    if (value > highestValue) {
      highestValue = value;
      highestKeys.length = 0;
      highestKeys.push(key);
    } else if (value === highestValue) {
      highestKeys.push(key);
    }
  });

  if (highestKeys.length > 1) {
    highestKeys[0] += ',';
  }

  return highestKeys;
};

function CareerContent() {
  const navigate = useNavigate();
  const { setLink } = useBreadcrumb();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleClick = () => {
    const screenWidth = window.innerWidth;
    if (screenWidth > 640) {
      setLink('Radar');
      navigate(`/dashboard/career/radar`, {
        state: { radarChart },
      });
    } else {
      setIsDrawerOpen(true);
    }
  };

  return (
    <>
      <div className="flex flex-col gap-2.5 items-center mt-3.5 max-w-[538px]">
        <h2 className="chart-title">RIASEC</h2>
        <div className="border border-[#E5E8EE] flex flex-col gap-10 items-center justify-center rounded-3xl w-full pt-[30px] pb-3.5 px-3">
          <RadarChart values={radarChart.values} />
          <Button
            label="Dive Deeper"
            variant="tertiary"
            fullWidth
            onClick={handleClick}
          />
        </div>
      </div>
      <CustomDrawer
        title={'RIASEC'}
        isOpen={isDrawerOpen}
        setIsDrawerOpen={setIsDrawerOpen}
      >
        <div className="flex flex-col gap-7 px-4">
          <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
            Your Results
          </h2>
          <p className="text-center text-lg font-medium leading-[22px] text-passiveLinkColor">
            Strongest trait{' '}
            {findHighestValues(radarChart).length > 1 ? 'are' : 'is'}{' '}
            {findHighestValues(radarChart).map((item, index) => (
              <span
                key={index}
                className="capitalize text-[#4A83F3] font-normal"
              >
                {item}{' '}
              </span>
            ))}
          </p>
          <p className="text-[#7A818A] leading-[22px] font-normal">
            {radarChart.description}
          </p>
          <div className="gap-9 flex flex-col items-center justify-center overflow-y-auto overflow-x-hidden">
            <RadarChart values={radarChart.values} />

            <div className="mt-3 mb-8">
              <SimilarProfileBadge peopleCount={253} />
            </div>
          </div>
        </div>
      </CustomDrawer>
    </>
  );
}

export { CareerContent };
