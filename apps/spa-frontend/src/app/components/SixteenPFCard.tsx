import { GradientLine } from './GradientLine';
import { Button } from './Button';
import { DashboardCardLayout } from './DashboardCardLayout';
import { useNavigate } from 'react-router-dom';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { useState } from 'react';
import { CustomDrawer } from './CustomDrawer';

interface DataProps {
  label: string;
  value: number;
  description: string;
}
export interface SixteenPFCardProps {
  title: string;
  data: DataProps[];
}

function SixteenPFCard({ title, data }: SixteenPFCardProps) {
  const navigate = useNavigate();
  const { setLink } = useBreadcrumb();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleClick = () => {
    const screenWidth = window.innerWidth;
    if (screenWidth > 640) {
      setLink(title);
      navigate(`/dashboard/personality/trait2/${title.toLocaleLowerCase()}`, {
        state: { title, data },
      });
    } else {
      setIsDrawerOpen(true);
    }
  };

  return (
    <>
      <DashboardCardLayout withTitle title={title}>
        <div className="flex flex-col px-3 pb-[15px] pt-[52px]">
          <div className="pl-[15px] pr-3 flex flex-col gap-5">
            {data.map((result, index) => (
              <GradientLine
                title={result.label}
                value={result.value}
                key={index}
                index={index}
                variant="secondary"
              />
            ))}
          </div>
          <div className="mt-[86px]">
            <Button
              label="Dive Deeper"
              variant="tertiary"
              fullWidth
              onClick={handleClick}
            />
          </div>
        </div>
      </DashboardCardLayout>
      <CustomDrawer
        title={title.toUpperCase()}
        isOpen={isDrawerOpen}
        setIsDrawerOpen={setIsDrawerOpen}
      >
        <div className="gap-9 flex flex-col overflow-y-auto px-4">
          <div className="flex flex-col gap-5">
            {/* <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
              Your Results
            </h2> */}
            <div className="flex flex-col gap-[34px]">
              {data.map((item, index) => {
                return (
                  <div key={index} className="flex flex-col">
                    <div className="text-passiveLinkColor font-medium leading-[19px] py-[7px] text-center px-0 md:px-[154px] md:max-w-max w-full max-w-full bg-[#F3F5F7] rounded-xl mb-12 whitespace-nowrap">
                      {item.label}
                    </div>
                    <GradientLine
                      title={item.label}
                      value={item.value}
                      key={index}
                      index={index}
                      variant="secondary"
                      isDrawer={true}
                    />
                    <p className="text-passiveLinkColor leading-[22px] mt-3.5">
                      {item.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="-mt-3 mb-8">
            {/* <SimilarProfileBadge peopleCount={253} /> */}
          </div>
        </div>
      </CustomDrawer>
    </>
  );
}

export { SixteenPFCard };
