import { SocialCard } from '../components/SocialCard';
import { RequireAuth } from '../providers/AuthProvider';
import { trpc } from '../utils/trpc';

function SocialPage() {
  const userMatches = trpc.private.getUserMatches.useQuery();

  return (
    <RequireAuth>
      <div className="flex flex-col py-3.5 px-6 gap-3.5">
        {/* <SocialFilter
            selectedFilters={selectedFilters}
            setSelectedFilters={setSelectedFilters}
            setSearchQuery={setSearchQuery}
            loading={loading}
          /> */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-5 gap-y-4">
          {userMatches.isFetched &&
            userMatches.data.map((userMatchOverview, index) => (
              <SocialCard
                key={index}
                //@ts-ignore
                userMatchOverview={userMatchOverview}
                loading={userMatches.isLoading}
              />
            ))}
        </div>
      </div>
    </RequireAuth>
  );
}

export { SocialPage };
