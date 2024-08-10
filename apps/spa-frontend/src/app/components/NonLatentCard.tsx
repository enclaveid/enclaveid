import classNames from 'classnames';
import { Button } from './Button';
import { PercentageCircle } from './PercentageCircle';
import { useState } from 'react';
import { TinyBarChart } from './TinyBarChart';
import { CardDetailsModal } from './CardDetailsModal';
import { DisplayableInterest } from '@enclaveid/shared';
import { SmallBadge } from './SmallBadge';

interface NonLatentCardProps {
  interest: DisplayableInterest;
}

function NonLatentCard({
  interest: {
    title,
    description,
    pipelineClusterId,
    isViewed: initViewed,
    activityDates,
    activityType,
    similarityPercentage,
  },
}: NonLatentCardProps) {
  const [isViewed, setIsViewed] = useState(initViewed);
  const [openModal, setOpenModal] = useState(false);

  // Truncate the description to 200 characters and add [...]
  const shortDescription =
    description.length > 170
      ? `${description.slice(0, 170)} [...]`
      : description;

  return (
    <article
      className={classNames(
        'pt-5 pb-[18px] pl-[13px] pr-[11px] rounded-xl  border  flex flex-col justify-between xl:max-w-[366px] gap-2.5',
        isViewed
          ? 'border-[#97CDC0] bg-[#F8FCFB]'
          : 'border-[#E5E8EE] bg-white',
      )}
    >
      <div className="flex flex-col gap-2.5">
        <h1 className="text-passiveLinkColor text-sm font-medium">
          [{pipelineClusterId}] {title}
        </h1>
        <SmallBadge variant={activityType} />
        <p className="text-passiveLinkColor text-sm ">{shortDescription}</p>
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
        <Button
          label="Expand"
          size="large"
          variant="primary"
          onClick={() => {
            setIsViewed(true);
            setOpenModal(true);
          }}
        />
      </div>
      <CardDetailsModal
        isOpen={openModal}
        closeModal={() => setOpenModal(false)}
        title={title}
        description={description}
      />
    </article>
  );
}

export { NonLatentCard };
