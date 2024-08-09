import classNames from 'classnames';
import { Button } from './Button';
import { PercentageCircle } from './PercentageCircle';
import { useState } from 'react';
import { TinyBarChart } from './TinyBarChart';

interface NonLatentCardProps {
  title: string;
  description: string;
  isSelected?: boolean;
  similarityPercentage?: number;
  activityDates?: string[];
}

function NonLatentCard({
  title,
  description,
  isSelected: initSelected,
  similarityPercentage,
  activityDates,
}: NonLatentCardProps) {
  const [isSelected, setIsSelected] = useState(initSelected);

  return (
    <article
      className={classNames(
        'pt-5 pb-[18px] pl-[13px] pr-[11px] rounded-xl  border  flex flex-col justify-between xl:max-w-[366px] gap-2.5',
        isSelected
          ? 'border-[#97CDC0] bg-[#F8FCFB]'
          : 'border-[#E5E8EE] bg-white',
      )}
    >
      <div className="flex flex-col gap-2.5">
        <h1 className="text-passiveLinkColor text-sm font-medium">{title}</h1>
        <p className="text-passiveLinkColor text-sm ">{description}</p>
      </div>
      <div className="flex items-center justify-between">
        {similarityPercentage && (
          <PercentageCircle
            percentage={similarityPercentage}
            size="md"
            label="Similarity"
          />
        )}
        {activityDates && <TinyBarChart dates={activityDates} />}
        <Button label="Expand" size="large" variant="primary" />
      </div>
    </article>
  );
}

export { NonLatentCard };
