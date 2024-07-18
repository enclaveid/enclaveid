import { useLocation } from 'react-router-dom';
import { findHighestValues } from './CareerContent';
import { RadarChart } from './RadarChart';

function RadarChartDetails() {
  const location = useLocation();
  const { radarChart } = location.state;

  return (
    <div className="flex flex-col gap-2.5 items-center mt-[34px] max-w-2xl">
      <h2 className="chart-title">RIASEC</h2>
      <div className="border border-[#E5E8EE] flex flex-col gap-10 items-center justify-center rounded-3xl w-full pt-[30px] pb-3.5 px-3">
        <h2 className="text-passiveLinkColor text-lg leadig-[22px] font-medium">
          Your Results
        </h2>
        <p className="text-center text-lg font-medium leading-[22px] text-passiveLinkColor">
          Strongest trait{' '}
          {findHighestValues(radarChart).length > 1 ? 'are' : 'is'}{' '}
          {findHighestValues(radarChart).map((item, index) => (
            <span key={index} className="capitalize text-[#4A83F3] font-normal">
              {item}{' '}
            </span>
          ))}
        </p>
        <RadarChart values={radarChart.values} />
        <p className="text-[#7A818A] leading-[22px] px-4">
          {radarChart.description}
        </p>
        <div className="mt-3 mb-8 max-w-max">
          {/* <SimilarProfileBadge peopleCount={253} /> */}
        </div>
      </div>
    </div>
  );
}

export { RadarChartDetails };
