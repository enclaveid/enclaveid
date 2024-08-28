import { MFTChart } from './MFTChart';
import { MFTChartData } from './mock-data';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CustomDrawer } from './CustomDrawer';
import { UnavailableChartOverlay } from './UnavailableChartOverlay';
import { DynamicAreaLoading } from './DynamicAreaLoading';

const mockData = MFTChartData;

export function MFTSection({
  data = mockData,
  isLoading,
}: {
  data?: typeof MFTChartData;
  isLoading?: boolean;
}) {
  const navigate = useNavigate();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const { setLink } = useBreadcrumb();
  const { description, ...circles } = MFTChartData;

  const handleClick = () => {
    const screenWidth = window.innerWidth;
    if (screenWidth > 640) {
      setLink('MFT');
      navigate(`/dashboard/politics/mft`, {
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
          <h2 className="chart-title">Moral Foundations Theory</h2>

          <UnavailableChartOverlay reason="no_data" enabled={data === mockData}>
            <MFTChart {...MFTChartData} handleClick={handleClick} />
          </UnavailableChartOverlay>
        </div>
      )}
      <CustomDrawer
        title={'Moral Foundations Theory'}
        isOpen={isDrawerOpen}
        setIsDrawerOpen={setIsDrawerOpen}
      >
        <div className="flex flex-col gap-7">
          {/* <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
            Your Results
          </h2> */}
          <div className="-mt-1 flex flex-col gap-[5px]">
            <p className="text-passiveLinkColor leading-[22px] max-w-[369px]">
              {MFTChartData.description}
            </p>
            <div className="md:max-w-[369px] max-w-full w-full py-[13px] bg-[#F3F5F7] rounded-xl text-passiveLinkColor text-[32px] leading-[38px] text-center flex items-center justify-center">
              Moderate
            </div>
          </div>
          <div className="gap-9 flex flex-col overflow-y-auto items-center relative">
            <MFTChart {...MFTChartData} handleClick={handleClick} />
            <div className="mt-3 mb-8 w-full">
              {/* <SimilarProfileBadge peopleCount={253} /> */}
            </div>
          </div>
        </div>
      </CustomDrawer>
    </>
  );
}
