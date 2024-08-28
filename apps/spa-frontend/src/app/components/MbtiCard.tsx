import { useState } from 'react';
import { Button } from './atoms/Button';
import { DashboardCardLayout } from './DashboardCardLayout';

import { useNavigate } from 'react-router-dom';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { CustomDrawer } from './CustomDrawer';
import { DynamicAreaLoading } from './DynamicAreaLoading';
import { mbtiCard } from './mock-data';
import { UnavailableChartOverlay } from './UnavailableChartOverlay';

const mockData = mbtiCard.data;

export interface MbtiCardProps {
  header?: string;
  label?: string;
  description?: string;
  data?: {
    title: string;
    content: string;
  };
  isLoading?: boolean;
}

function MbtiCard({
  header = 'MBTI',
  label = mbtiCard.label,
  description = mbtiCard.description,
  data = mockData,
  isLoading,
}: MbtiCardProps) {
  const navigate = useNavigate();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const { setLink } = useBreadcrumb();

  const handleClick = () => {
    const screenWidth = window.innerWidth;
    if (screenWidth > 640) {
      setLink(label);
      navigate(`/dashboard/personality/mbti/${label.toLocaleLowerCase()}`, {
        state: { data, label },
      });
    } else {
      setIsDrawerOpen(true);
    }
  };
  return (
    <>
      <DashboardCardLayout withTitle title={header}>
        {isLoading ? (
          <DynamicAreaLoading />
        ) : (
          <UnavailableChartOverlay reason="no_data" enabled={data === mockData}>
            <div className="flex flex-col gap-4 sm:gap-[5px] px-4 sm:px-3 pt-8 sm:pt-[9px] pb-[15px] ">
              <h1 className="text-[64px] leading-[75px] text-[#30A78A] text-center">
                {label}
              </h1>
              <p className="text-[#6C7A8A] leading-[22px] sm:px-3 whitespace-pre-line">
                {description}
              </p>
              <div className="sm:mt-0 mt-4">
                <Button
                  label="Dive Deeper"
                  variant="tertiary"
                  fullWidth
                  onClick={handleClick}
                />
              </div>
            </div>
          </UnavailableChartOverlay>
        )}
      </DashboardCardLayout>
      <CustomDrawer
        title={'Myers-Briggs Type Indicator'}
        isOpen={isDrawerOpen}
        setIsDrawerOpen={setIsDrawerOpen}
      >
        <div className="gap-4 flex flex-col overflow-y-auto px-3">
          <div className="flex flex-col gap-5">
            {/* <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
              Your Results
            </h2> */}
            <div className="py-4 text-[#30A78A] w-full text-[64px] leading-[75px] text-center bg-[#F3F5F7] rounded-xl">
              {label}
            </div>
          </div>
          <div dangerouslySetInnerHTML={{ __html: data.content }} />
          <div className="mt-4 mb-8">
            {/* <SimilarProfileBadge peopleCount={253} /> */}
          </div>
        </div>
      </CustomDrawer>
    </>
  );
}

export { MbtiCard };
