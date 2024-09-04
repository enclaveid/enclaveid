import classNames from 'classnames';
import { Button } from './atoms/Button';
import { PercentageCircle } from './atoms/PercentageCircle';
import { useState } from 'react';
import { TinyBarChart } from './TinyBarChart';
import { CardDetailsModal } from './CardDetailsModal';
import { DisplayableInterest } from '@enclaveid/shared';
import { SmallBadge } from './atoms/SmallBadge';

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
    isSensitive,
    socialLikelihood,
    clusterItems,
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
        'pt-5 pb-[18px] pl-[13px] pr-[11px] rounded-xl  border  flex flex-col justify-between min-h-[280px] max-h-[280px] max-w-[366px] gap-2.5',
        isViewed
          ? 'border-[#97CDC0] bg-[#F8FCFB]'
          : 'border-[#E5E8EE] bg-white',
      )}
    >
      <div className="flex flex-col gap-2.5">
        <h1 className="text-passiveLinkColor text-sm font-medium">
          [{pipelineClusterId}] {title}
        </h1>
        <div className="flex gap-2">
          <SmallBadge variant={activityType} />
          {isSensitive && <SmallBadge variant="sensitive" />}
        </div>
        <p className="text-passiveLinkColor text-sm ">{shortDescription}</p>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-2">
          {socialLikelihood && (
            <PercentageCircle
              percentage={socialLikelihood}
              size="md"
              label="Relevance"
            />
          )}
          {similarityPercentage && (
            <PercentageCircle
              percentage={similarityPercentage}
              size="md"
              label="Similarity"
            />
          )}
        </div>
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
        description={
          description +
          (clusterItems?.length
            ? '\n\n**Timeline**\n\n' +
              clusterItems.slice().reverse().join('\n\n')
            : '')
        }
      />
    </article>
  );
}

export { NonLatentCard };
