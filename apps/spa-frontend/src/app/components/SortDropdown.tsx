import { Menu } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';

type SortOption = 'prevalence' | 'time';

interface SortDropdownProps {
  currentSort: SortOption;
  onSortChange: (option: SortOption) => void;
}

export function SortDropdown({ currentSort, onSortChange }: SortDropdownProps) {
  return (
    <Menu as="div" className="relative inline-block text-left w-56">
      <div>
        <Menu.Button className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-3 py-2 text-sm  text-passiveLinkColor shadow-sm ring-1 ring-inset ring-[#E5E8EE] hover:bg-gray-50">
          Primary sort: <span className="font-medium">{currentSort}</span>
          <ChevronDownIcon
            className="-mr-1 h-5 w-5 text-passiveIconColor"
            aria-hidden="true"
          />
        </Menu.Button>
      </div>

      <Menu.Items className="absolute z-10 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
        <div className="py-1">
          <Menu.Item>
            {({ active }) => (
              <button
                onClick={() => onSortChange('prevalence')}
                className={`${
                  active ? 'bg-greenBg text-white' : 'text-passiveLinkColor'
                } block px-4 py-2 text-sm w-full text-left`}
              >
                Prevalence
              </button>
            )}
          </Menu.Item>
          <Menu.Item>
            {({ active }) => (
              <button
                onClick={() => onSortChange('time')}
                className={`${
                  active ? 'bg-greenBg text-white' : 'text-passiveLinkColor'
                } block px-4 py-2 text-sm w-full text-left`}
              >
                Time
              </button>
            )}
          </Menu.Item>
        </div>
      </Menu.Items>
    </Menu>
  );
}
