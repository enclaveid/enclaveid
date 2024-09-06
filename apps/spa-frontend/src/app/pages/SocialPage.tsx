import { SocialCard } from '../components/SocialCard';
import { trpc } from '../utils/trpc';
import { userMatches as mockData } from '../utils/mock-data';
import { UnavailableChartOverlay } from '../components/UnavailableChartOverlay';
import { LoadingPage } from './LoadingPage';
function SocialPage() {
  const userMatches = trpc.private.getUserMatches.useQuery();

  const data = userMatches.data?.length ? userMatches.data : mockData;

  return userMatches.isLoading ? (
    <LoadingPage />
  ) : (
    <UnavailableChartOverlay>
      <div className="flex flex-col py-3.5 px-6 gap-3.5">
        {/* <SocialFilter
            selectedFilters={selectedFilters}
            setSelectedFilters={setSelectedFilters}
            setSearchQuery={setSearchQuery}
            loading={loading}
          /> */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-5 gap-y-4">
          {data.map((userMatchOverview, index) => (
            <SocialCard
              key={index}
              //@ts-ignore
              userMatchOverview={userMatchOverview}
              loading={userMatches.isLoading}
            />
          ))}
        </div>
      </div>
    </UnavailableChartOverlay>
  );
}

export { SocialPage };
