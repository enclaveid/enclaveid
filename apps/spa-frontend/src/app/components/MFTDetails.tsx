import { useLocation } from 'react-router-dom';
import { MFTChart } from './MFTChart';
import Markdown from 'react-markdown';

interface Props {
  circles: {
    harm: number;
    fairness: number;
    authority: number;
    ingroup: number;
    purity: number;
  };
  description: string;
}

function MFTDetails() {
  const location = useLocation();
  const { description, circles } = location.state as Props;

  return (
    <div className="flex rounded-3xl px-6 xl:flex-row flex-col">
      <div className="xl:max-w-[499px] pr-6 xl:pb-0 pb-10">
        {/* <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
          Your Results
        </h2> */}
        <div className="flex flex-col gap-8 w-full mt-7">
          {/* <div className="w-full py-[13px] bg-[#F3F5F7] rounded-xl text-passiveLinkColor text-[32px] leading-[38px] text-center flex items-center justify-center">
            Moderate
          </div>
          <p className="text-passiveLinkColor leading-[22px]">{description}</p> */}
          <Markdown className="text-passiveLinkColor whitespace-pre-wrap">
            {description}
          </Markdown>
          {/* <SimilarProfileBadge peopleCount={253} /> */}
        </div>
      </div>
      <div className="gap-9 flex flex-col overflow-y-auto items-center justify-center shrink-0 xl:max-w-[545px] w-full xl:pt-0 pt-10">
        <MFTChart mftChartAvailable={false} {...circles} />
      </div>
    </div>
  );
}

export { MFTDetails };
