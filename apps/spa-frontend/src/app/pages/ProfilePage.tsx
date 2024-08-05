import { useLocation } from 'react-router-dom';
import { SocialCard } from '../components/SocialCard';
import { useEffect, useState } from 'react';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { RequireAuth } from '../providers/AuthProvider';
import { SimilarInterestsCharts } from '../components/SimilarInterestsCharts';
import { UserMatchOverview } from '@enclaveid/shared';
import { trpc } from '../utils/trpc';
import { LoadingPage } from './LoadingPage';

const tabs = [
  { title: 'Personality', path: '/socials/:title/personality' },
  { title: 'Politics', path: '/socials/:title/politics' },
  { title: 'Career', path: '/socials/:title/career' },
];

function ProfilePage() {
  const location = useLocation();
  const { setLink } = useBreadcrumb();
  const [usernamePath, setUsernamePath] = useState('');

  useEffect(() => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const usernameSlug = pathSegments[pathSegments.length - 1];
    const formattedName = formatUsernameFromPath(usernameSlug);
    setLink(formattedName);
    setUsernamePath(usernameSlug);
  }, [location.pathname]);

  const userTabs = tabs.map((tab) => ({
    title: tab.title,
    path: `/socials/${usernamePath}/${tab.title.toLowerCase()}`,
  }));

  function formatUsernameFromPath(pathname: string): string {
    const usernameSlug = pathname.split('/').pop();

    if (!usernameSlug) return '';

    const formattedName = usernameSlug
      .split('-')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');

    return `${formattedName}'s Profile`;
  }

  useEffect(() => {
    setLink(formatUsernameFromPath(location.pathname));
  }, [location.pathname]);

  const userMatchOverview = location.state
    .userMatchOverview as UserMatchOverview;

  const matchDetailsQuery = trpc.private.getUserMatchDetails.useQuery({
    usersOverallSimilarityId: userMatchOverview.usersOverallSimilarityId,
  });

  return (
    <RequireAuth>
      <div className="px-4 mt-5 pb-2">
        <SocialCard userMatchOverview={userMatchOverview} />
      </div>
      {matchDetailsQuery.isLoading ? (
        <LoadingPage />
      ) : (
        <SimilarInterestsCharts
          proactiveInterests={matchDetailsQuery.data.proactiveInterests}
          reactiveInterests={matchDetailsQuery.data.reactiveInterests}
        />
      )}
      {/* <Tabs tabs={userTabs} /> */}
    </RequireAuth>
  );
}

export { ProfilePage };
