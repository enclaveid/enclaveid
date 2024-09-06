import { useLocation } from 'react-router-dom';
import { MbtiCardProps } from './MbtiCard';
import Markdown from 'react-markdown';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { useEffect } from 'react';

function MbtiCardDetails() {
  const location = useLocation();
  const { data, label } = location.state as MbtiCardProps;
  const { setLink } = useBreadcrumb();

  useEffect(() => {
    setLink('MBTI');
  }, [setLink]);

  return (
    <div className="max-w-4xl sm:px-0 px-4">
      <div className="flex flex-col gap-5">
        {/* <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
          Your Results
        </h2> */}
        <div className="py-4 text-[#30A78A] px-[120px] md:max-w-max w-full max-w-full text-[64px] leading-[75px] text-center bg-[#F3F5F7] rounded-xl">
          {label}
        </div>
      </div>
      <Markdown className="text-[#6C7A8A]  whitespace-pre-line p-4">
        {data.content}
      </Markdown>
    </div>
  );
}
export { MbtiCardDetails };
