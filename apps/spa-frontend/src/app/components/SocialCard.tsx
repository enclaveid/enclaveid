import { Link } from 'react-router-dom';
import { LocationPinIcon } from './atoms/Icons';
import { getIdenticon } from '../utils/ui/identicons';
import { UserMatchOverview } from '@enclaveid/shared';
import { LoadingCard } from './LoadingCard';
import { PercentageCircle } from './atoms/PercentageCircle';
import { Button } from './atoms/Button';

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
        <div className="flex flex-col">
          <PercentageCircle
            percentage={overallSimilarity}
            size="lg"
            label="Overall match"
          />
          <Button label="Open chat" size="small" className="mt-5" />
        </div>
      </div>
    </Link>
  );
}

export { SocialCard };
