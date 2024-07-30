import { useState } from 'react';
import { SocialCard } from '../components/SocialCard';
import { userData } from '../components/mock-data';
import { RequireAuth } from '../providers/AuthProvider';
function SocialPage() {
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const filteredUsers = userData.filter(
    (user) =>
      (selectedFilters.length === 0 || selectedFilters.includes(user.type)) &&
      (user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.location.toLowerCase().includes(searchQuery.toLowerCase())),
  );

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
          {filteredUsers.map((user, index) => (
            <SocialCard key={index} {...user} loading={loading} />
          ))}
        </div>
      </div>
    </RequireAuth>
  );
}

export { SocialPage };
