import React, { useState } from 'react';
import { trpc } from '../utils/trpc';
import { NonLatentCard } from './NonLatentCard';
import { VirtuosoGrid } from 'react-virtuoso';
import { DisplayableInterest } from '@enclaveid/shared';
import { LoadingPage } from '../pages/LoadingPage';
import { UnavailableChartOverlay } from './UnavailableChartOverlay';
import { ownInterests as mockData } from '../utils/mock-data';
import { SortDropdown } from './SortDropdown';

export function OwnInterests() {
  const [currentSort, setCurrentSort] = useState<'prevalence' | 'time'>(
    'prevalence',
  );

  const interestsQuery = trpc.private.getUserInterests.useInfiniteQuery(
    {
      limit: 20,
      sort: currentSort,
    },
    {
      getNextPageParam: (lastPage) => lastPage.nextCursor,
    },
  );

  const allInterests =
    interestsQuery.data?.pages.flatMap((page) => page.userInterests) ||
    mockData;

  const fetchMore = () => {
    interestsQuery.hasNextPage && interestsQuery.fetchNextPage();
  };

  return interestsQuery.isLoading ? (
    <LoadingPage />
  ) : (
    <UnavailableChartOverlay>
      <div className="flex justify-start mb-4 px-6">
        <SortDropdown currentSort={currentSort} onSortChange={setCurrentSort} />
      </div>
      <VirtuosoGrid
        style={{ height: '85vh', width: '100%' }}
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
    </UnavailableChartOverlay>
  );
}
