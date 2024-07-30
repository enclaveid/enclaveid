import classNames from 'classnames';
import { getIdenticon } from '../utils/ui/identicons';

interface SimilarProfileBadgeProps {
  peopleCount: number;
  url?: string;
  variant?: 'sm';
}

const randomUsernames = Array.from({ length: 5 }, () =>
  Array.from({ length: 10 }, () => Math.floor(Math.random() * 10)).join(''),
);

function SimilarProfileBadge({
  peopleCount = 1123,
  url,
  variant,
}: SimilarProfileBadgeProps) {
  return (
    <div
      className={classNames(
        'bg-white pl-[9px] pr-[17px] border border-[#E5E8EE] rounded-xl w-full',
        variant === 'sm' ? 'py-1.5 shadow' : 'pt-[15px] pb-[13px]',
      )}
    >
      <div className="flex items-center gap-2.5">
        <div className="flex -space-x-2 overflow-hidden shrink-0">
          {randomUsernames.map((username, index) => (
            <img
              key={index}
              className="inline-block h-[27px] w-[27px] rounded-full"
              src={getIdenticon(username)}
              alt=""
            />
          ))}
        </div>
        <span className="text-[#6C7A8A] text-xs">
          {`${peopleCount.toLocaleString()} users on the platform`}
        </span>
      </div>
    </div>
  );
}

export { SimilarProfileBadge };
