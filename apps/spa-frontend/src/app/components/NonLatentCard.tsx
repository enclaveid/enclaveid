import classNames from 'classnames';

interface NonLatentCardProps {
  title: string;
  description: string;
  isSelected?: boolean;
}

function NonLatentCard({ title, description, isSelected }: NonLatentCardProps) {
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
      {/* <SimilarProfileBadge peopleCount={16} variant="sm" /> */}
    </article>
  );
}

export { NonLatentCard };
