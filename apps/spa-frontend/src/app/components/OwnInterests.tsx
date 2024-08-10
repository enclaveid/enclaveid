import React from 'react';
import { trpc } from '../utils/trpc';
import { NonLatentCard } from './NonLatentCard';
import { VirtuosoGrid } from 'react-virtuoso';
import { DisplayableInterest } from '@enclaveid/shared';

export function OwnInterests() {
  const interestsQuery = trpc.private.getUserInterests.useInfiniteQuery(
    {
      limit: 20,
    },
    {
      getNextPageParam: (lastPage) => lastPage.nextCursor,
    },
  );

  const allInterests =
    interestsQuery.data?.pages.flatMap((page) => page.userInterests) || [];

  const fetchMore = () => {
    interestsQuery.hasNextPage && interestsQuery.fetchNextPage();
  };

  return (
    <VirtuosoGrid
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
  );
}
