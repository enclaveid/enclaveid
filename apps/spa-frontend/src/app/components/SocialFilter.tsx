import { Menu, Transition } from '@headlessui/react';
import { Dispatch, Fragment } from 'react';
import { RemoveIcon, SearchIcon } from './atoms/Icons';
import { userData } from './mock-data';
import classNames from 'classnames';

interface FilterProps {
  selectedFilters: string[];
  setSelectedFilters: Dispatch<React.SetStateAction<string[]>>;
  setSearchQuery: Dispatch<React.SetStateAction<string>>;
  loading: boolean;
}

function SocialFilter({
  selectedFilters,
  setSelectedFilters,
  setSearchQuery,
  loading,
}: FilterProps) {
  const uniqueFilterTypes = Array.from(
    new Set(userData.map((user) => user.type)),
  ).filter((filter) => !selectedFilters.includes(filter));

  const toggleFilter = (filter: string) => {
    setSelectedFilters((filters) =>
      filters.includes(filter)
        ? filters.filter((f) => f !== filter)
        : [...filters, filter],
    );
  };

  const clearFilters = () => setSelectedFilters([]);

  return (
    <div
      className={classNames(
        'flex flex-col gap-3.5 transition-opacity',
        loading ? 'opacity-0' : 'opacity-100',
      )}
    >
      <div className="flex min-[810px]:items-center justify-between gap-x-4 gap-y-8 min-[810px]:flex-row flex-col">
        <div className="min-[810px]:max-w-[340px] w-full relative ">
          <input
            type="text"
            placeholder="Search for people or activities..."
            className="outline outline-1 outline-[#E5E8EE] text-passiveLinkColor font-sm leading-4 py-2 pl-8 pr-4 w-full rounded-md"
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="pointer-events-none absolute top-1/2 -translate-y-1/2 left-2.5">
            <SearchIcon />
          </button>
        </div>
        <div className="flex gap-2.5 items-center min-[810px]:justify-start justify-end z-20">
          {selectedFilters.length > 0 && (
            <button
              onClick={clearFilters}
              className="font-medium text-sm leading-4 text-greenBg outline outline-1 outline-greenBg rounded-md py-2 px-3"
            >
              Clear Filters
            </button>
          )}
          <Menu as="div" className="relative inline-block text-left">
            <div>
              <Menu.Button className="inline-flex w-full justify-center rounded-md focus:outline-none bg-greenBg py-2 px-8 outline outline-1 outline-[#DBDBDB] text-white font-medium text-sm leading-4">
                Filters
              </Menu.Button>
            </div>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right divide-y divide-gray-100 rounded-md bg-white shadow-lg ring-1 ring-black/5 focus:outline-none">
                {uniqueFilterTypes.map((filter) => (
                  <div className="px-1 py-1" key={filter}>
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={() => toggleFilter(filter)}
                          className={`group flex w-full items-center rounded-md px-2 py-2 text-sm ${active ? 'bg-greenBg text-white' : 'text-gray-900'}`}
                        >
                          {filter}
                        </button>
                      )}
                    </Menu.Item>
                  </div>
                ))}
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
      <div className="flex items-center min-[810px]:justify-end justify-center gap-2.5 flex-wrap">
        {selectedFilters.map((filter) => (
          <button
            key={filter}
            className="flex items-center gap-2 px-2 py-1.5 outline outline-1 outline-[#E5E8EE] rounded-full whitespace-nowrap"
            onClick={() => toggleFilter(filter)}
          >
            <span className="text-passiveLinkColor font-medium leading-[14px] text-xs">
              Similar on {filter.toUpperCase()}
            </span>
            <RemoveIcon />
          </button>
        ))}
      </div>
    </div>
  );
}

export { SocialFilter };
