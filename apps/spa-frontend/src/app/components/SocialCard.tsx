import { Link } from 'react-router-dom';
import { LocationPinIcon } from './Icons';
import classNames from 'classnames';
import { getIdenticon } from '../utils/ui/identicons';
import { UserMatchOverview } from '@enclaveid/shared';
import { LoadingCard } from './LoadingCard';

interface SocialCardProps {
  userMatchOverview?: UserMatchOverview;
  loading?: boolean;
}

function SocialCard({ userMatchOverview, loading }: SocialCardProps) {
  if (loading) return <LoadingCard />;

  const { displayName, gender, humanReadableGeography, overallSimilarity } =
    userMatchOverview;

  const formattedLink = (displayName: string) => {
    return displayName
      .split(' ')
      .map((word) => word.toLowerCase())
      .join('-');
  };

  const formattedPercentage = (raw: number) => {
    return (raw * 100).toFixed(2);
  };

  const getMatchBackgroundColor = (percentage: number) => {
    if (percentage < 0.5) return 'bg-[#FF5C00]/10 text-[#FF5C00]';
    // if (percentage < 0.8) return 'bg-[#2F5FA6]/20 text-[#2F5FA6]';

    return 'bg-greenBg/10 text-greenBg';
  };

  return (
    <Link
      to={`/socials/${formattedLink(displayName)}`}
      state={{ userMatchOverview }}
      className="p-6 flex items-center gap-4 border border-[#E5E8EE] rounded-3xl"
    >
      <img
        src={getIdenticon(displayName)}
        alt=""
        className="w-[101px] h-[101px] rounded-full"
      />
      <div className="flex justify-between w-full flex-wrap gap-3">
        <div className="flex flex-col">
          <h4 className="text-passiveLinkColor font-medium text-2xl leading-7">
            {displayName}
          </h4>

          <h5 className="text-passiveLinkColor font-medium leading-[18px] mt-[9px]">
            {gender}
          </h5>
          <div className="flex items-center gap-2 mt-3">
            <LocationPinIcon />
            <h6 className="text-passiveLinkColor font-medium leading-[18px]">
              {humanReadableGeography}
            </h6>
          </div>
        </div>
        <div>
          <div
            className={classNames(
              'p-2.5 rounded-full text-sm leading-[16.4px] font-medium',
              getMatchBackgroundColor(overallSimilarity),
            )}
          >
            {formattedPercentage(overallSimilarity)}% overall match
          </div>
        </div>
      </div>
    </Link>
  );
}

export { SocialCard };
