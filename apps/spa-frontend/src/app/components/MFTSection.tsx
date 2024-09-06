import { MFTChart } from './MFTChart';
import { MFTChartData } from '../utils/mock-data';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CustomDrawer } from './CustomDrawer';
import { UnavailableChartOverlay } from './UnavailableChartOverlay';
import { DynamicAreaLoading } from './DynamicAreaLoading';
import Markdown from 'react-markdown';

const mockData = MFTChartData;

export interface MFTSectionProps {
  data?: typeof MFTChartData;
  isLoading?: boolean;
}

export function MFTSection({ data = mockData, isLoading }: MFTSectionProps) {
  const navigate = useNavigate();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const { description, ...circles } = data;

  const handleClick = () => {
    const screenWidth = window.innerWidth;
    if (screenWidth > 640) {
      navigate(`mft`, {
        state: { circles, description },
      });
    } else {
      setIsDrawerOpen(true);
    }
  };
  return (
    <>
      {isLoading ? (
        <DynamicAreaLoading />
      ) : (
        <div className="flex flex-col gap-2.5 items-center">
          <h2 className="chart-title">Moral Foundations</h2>

          <UnavailableChartOverlay
            enabled={data === mockData}
            questionnaireStatusKey="isMoralFoundationsComplete"
          >
            <MFTChart {...data} handleClick={handleClick} />
          </UnavailableChartOverlay>
        </div>
      )}
      <CustomDrawer
        title={'Moral Foundations'}
        isOpen={isDrawerOpen}
        setIsDrawerOpen={setIsDrawerOpen}
      >
        <div className="flex flex-col gap-7">
          {/* <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
            Your Results
          </h2> */}
          <div className="-mt-1 flex flex-col gap-[5px]">
            <Markdown>{data.description}</Markdown>
            {/* <div className="md:max-w-[369px] max-w-full w-full py-[13px] bg-[#F3F5F7] rounded-xl text-passiveLinkColor text-[32px] leading-[38px] text-center flex items-center justify-center">
              Moderate
            </div> */}
          </div>
          <div className="gap-9 flex flex-col overflow-y-auto items-center relative">
            <MFTChart {...data} handleClick={handleClick} />
            <div className="mt-3 mb-8 w-full">
              {/* <SimilarProfileBadge peopleCount={253} /> */}
            </div>
          </div>
        </div>
      </CustomDrawer>
    </>
  );
}
