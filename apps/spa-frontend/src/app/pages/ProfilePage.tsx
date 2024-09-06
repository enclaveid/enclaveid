import { useLocation } from 'react-router-dom';
import { SocialCard } from '../components/SocialCard';
import { useEffect, useState, useCallback } from 'react';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { RequireAuth } from '../providers/AuthProvider';
import { DisplayableInterest, UserMatchOverview } from '@enclaveid/shared';
import { trpc } from '../utils/trpc';
import { VirtuosoGrid } from 'react-virtuoso';
import { NonLatentCard } from '../components/NonLatentCard';
import { Tabs } from '../components/Tabs';
import { LoadingPage } from './LoadingPage';
import React from 'react';

const tabs = [
  { title: 'Interests', path: '/dashboard/socials/:title/interests' },
  { title: 'Personality', path: '/dashboard/socials/:title/personality' },
  { title: 'Politics', path: '/dashboard/socials/:title/politics' },
  { title: 'Career', path: '/dashboard/socials/:title/career' },
];

function ProfilePage() {
  const location = useLocation();
  const { setLink } = useBreadcrumb();
  const [usernamePath, setUsernamePath] = useState('');

  const formatUsernameFromPath = useCallback((pathname: string): string => {
    const usernameSlug = pathname.split('/').pop();
    if (!usernameSlug) return '';

    const formattedName = usernameSlug
      .split('-')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');

    return `${formattedName}'s Profile`;
  }, []);

  useEffect(() => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const usernameSlug = pathSegments[pathSegments.length - 1];
    const formattedName = formatUsernameFromPath(usernameSlug);
    setLink(formattedName);
    setUsernamePath(usernameSlug);
  }, [location.pathname, setLink, formatUsernameFromPath]);

  const userTabs = tabs.map((tab) => ({
    title: tab.title,
    path: `/dashboard/socials/${usernamePath}/${tab.title.toLowerCase()}`,
  }));

  const userMatchOverview = location.state
    .userMatchOverview as UserMatchOverview;

  const matchDetailsQuery = trpc.private.getUserMatchDetails.useInfiniteQuery(
    {
      usersOverallSimilarityId: userMatchOverview.usersOverallSimilarityId,
    },
    {
      getNextPageParam: (lastPage) => lastPage.interests.nextCursor,
    },
  );

  const allInterests =
    matchDetailsQuery.data?.pages.flatMap(
      (page) => page.interests.userInterests,
    ) || [];

  const fetchMore = useCallback(() => {
    matchDetailsQuery.hasNextPage && matchDetailsQuery.fetchNextPage();
  }, [matchDetailsQuery]);

  return (
    <RequireAuth>
      <div className="px-4 pb-2">
        <SocialCard userMatchOverview={userMatchOverview} />
      </div>
      {matchDetailsQuery.isLoading ? (
        <LoadingPage />
      ) : (
        <>
          <Tabs tabs={userTabs} />
          <InterestGrid
            interests={allInterests as DisplayableInterest[]}
            fetchMore={fetchMore}
          />
        </>
      )}
    </RequireAuth>
  );
}

interface InterestGridProps {
  interests: DisplayableInterest[];
  fetchMore: () => void;
}

function InterestGrid({ interests, fetchMore }: InterestGridProps) {
  return (
    <VirtuosoGrid
      className="mt-3"
      style={{ height: '100vh', width: '100%' }}
      totalCount={interests.length}
      overscan={200}
      endReached={fetchMore}
      itemContent={(index) => (
        <NonLatentCard interest={interests[index] as DisplayableInterest} />
      )}
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
  );
}

export { ProfilePage };
