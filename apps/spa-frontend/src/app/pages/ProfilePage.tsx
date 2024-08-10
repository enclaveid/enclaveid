import { useLocation } from 'react-router-dom';
import { SocialCard } from '../components/SocialCard';
import { useEffect, useState } from 'react';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { RequireAuth } from '../providers/AuthProvider';
import { DisplayableInterest, UserMatchOverview } from '@enclaveid/shared';
import { trpc } from '../utils/trpc';
import { LoadingCard } from '../components/LoadingCard';
import React from 'react';
import { VirtuosoGrid } from 'react-virtuoso';
import { NonLatentCard } from '../components/NonLatentCard';
import { Tabs } from '../components/Tabs';

const tabs = [
  { title: 'Interests', path: '/socials/:title/interests' },
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
  }, [location.pathname, setLink]);

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
  }, [location.pathname, setLink]);

  const userMatchOverview = location.state
    .userMatchOverview as UserMatchOverview;

  const matchDetailsQuery = trpc.private.getUserMatchDetails.useInfiniteQuery(
    {
      usersOverallSimilarityId: userMatchOverview.usersOverallSimilarityId,
      // activityTypes: ['proactive'],
    },
    {
      getNextPageParam: (lastPage) => lastPage.interests.nextCursor,
    },
  );

  const allInterests =
    matchDetailsQuery.data?.pages.flatMap(
      (page) => page.interests.userInterests,
    ) || [];

  const fetchMore = () => {
    matchDetailsQuery.hasNextPage && matchDetailsQuery.fetchNextPage();
  };

  return (
    <RequireAuth>
      <div className="px-4 mt-5 pb-2">
        <SocialCard userMatchOverview={userMatchOverview} />
      </div>
      {matchDetailsQuery.isLoading ? (
        <>
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
        </>
      ) : (
        <>
          <Tabs tabs={userTabs} />

          <VirtuosoGrid
            className="mt-3"
            style={{ height: '100vh', width: '100%' }}
            totalCount={allInterests.length}
            overscan={200}
            endReached={fetchMore}
            itemContent={(index) => {
              return (
                <NonLatentCard
                  interest={allInterests[index] as DisplayableInterest}
                />
              );
            }}
            components={{
              List: React.forwardRef((props, ref) => (
                <div
                  {...props}
                  ref={ref}
                  className="flex flex-row flex-wrap gap-6 px-6"
                />
              )),
            }}
            listClassName="flex flex-row flex-wrap gap-6 px-6"
          />
        </>
      )}
    </RequireAuth>
  );
}

export { ProfilePage };
