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

  const { displayName, gender, country, overallSimilarity } = userMatchOverview;

  const formattedLink = (displayName: string) => {
    return displayName
      .split(' ')
      .map((word) => word.toLowerCase())
      .join('-');
  };

  return (
    <Link
      to={`/dashboard/socials/${formattedLink(displayName)}`}
      state={{ userMatchOverview }}
      className="p-3 flex items-center gap-3 border border-[#E5E8EE] rounded-xl"
    >
      <img
        src={getIdenticon(displayName)}
        alt=""
        className="w-10 h-10 rounded-full"
      />
      <div className="flex-grow flex justify-between items-center">
        <div className="flex items-center gap-2">
          <h4 className="text-passiveLinkColor font-medium text-lg">
            {displayName}
          </h4>
          <span className="text-passiveLinkColor text-sm">•</span>
          <span className="text-passiveLinkColor text-sm">{gender}</span>
          <span className="text-passiveLinkColor text-sm">•</span>
          <div className="flex items-center gap-1">
            <LocationPinIcon />
            <span className="text-passiveLinkColor text-sm">{country}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <PercentageCircle
            percentage={overallSimilarity}
            size="md"
            label="Match"
          />
          <Button
            label="Open chat"
            size="small"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
            }}
          />
        </div>
      </div>
    </Link>
  );
}

export { SocialCard };
