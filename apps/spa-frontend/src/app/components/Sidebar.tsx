import { SidebarSection } from './SidebarSection';
import { SidebarItem } from './SidebarItem';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Bars3Icon } from '@heroicons/react/24/outline';
import { ArrowLeftStartOnRectangleIcon } from '@heroicons/react/24/outline';
import { CogIcon } from '@heroicons/react/24/outline';
import { SimilarProfileBadge } from './SimilarProfileBadge';
import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Logo } from './Logo';
import { sidebarItems } from '../utils/ui/sidebarItems';
import { trpc } from '../utils/trpc';

export interface SidebarProps {
  onLogout?: () => void;
}

function renderSidebarItems() {
  return Object.entries(sidebarItems).map(([title, items]) => (
    <SidebarSection title={title} key={title}>
      {items.map((item) => (
        <SidebarItem
          key={item.text}
          icon={<item.icon />}
          text={item.text}
          href={item.href}
          chip={item.chip}
        />
      ))}
    </SidebarSection>
  ));
}

function Sidebar(props: SidebarProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { onLogout } = props;

  const peopleCount = trpc.private.getPeopleCount.useQuery().data;

  return (
    <aside className="w-full sm:w-[296px] bg-[#F3F5F7] px-[18px] sm:px-[22px] flex flex-col sm:h-full h-max border-b border-b-[#E5E8EE] sm:border-none relative">
      <div className="pb-3.5 sm:pb-[54px] pt-[55px] sm:pt-12 sm:border-b border-b-[#E5E8EE] flex items-center justify-between">
        {/* <h1 className="text-passiveLinkColor text-xl leading-6 sm:text-4xl sm:leading-[42px] tracking-[-0.02em] text-center">
          EnclaveID
        </h1> */}
        <Logo isSmall />
        <button
          className="sm:hidden"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <Bars3Icon className="w-5 h-5 text-passiveLinkColor" />
        </button>
      </div>
      <div className="sm:flex hidden flex-col justify-between flex-1 py-5">
        <div className="flex flex-col gap-[18px]">
          {renderSidebarItems()}
          <SimilarProfileBadge peopleCount={peopleCount} />
        </div>
        <SidebarSection noGap={true}>
          <SidebarItem
            icon={<CogIcon />}
            text="Account and Settings"
            href="/account-settings"
          />
          <SidebarItem
            icon={<ArrowLeftStartOnRectangleIcon />}
            text="Log out"
            onClick={onLogout}
          />
        </SidebarSection>
      </div>
      <div className="sm:hidden block pb-[18px]">
        <SimilarProfileBadge peopleCount={peopleCount} />
      </div>{' '}
      <Transition.Root show={sidebarOpen} as={Fragment}>
        <Dialog className="relative z-50 lg:hidden" onClose={setSidebarOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button
                      type="button"
                      className="-m-2.5 p-2.5"
                      onClick={() => setSidebarOpen(false)}
                    >
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon
                        className="h-6 w-6 text-white"
                        aria-hidden="true"
                      />
                    </button>
                  </div>
                </Transition.Child>
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-[#F3F5F7] px-6 pb-4">
                  <div className="pt-12 pb-3.5 px-4">
                    <h1 className="text-passiveLinkColor text-4xl leading-[42px] tracking-[-0.02em] text-center">
                      EnclaveID
                    </h1>
                  </div>
                  <div className="flex flex-col justify-between flex-1 py-5">
                    <div className="flex flex-col gap-[18px]">
                      {renderSidebarItems()}
                      <SimilarProfileBadge peopleCount={peopleCount} />
                    </div>
                    <SidebarSection noGap={true}>
                      <SidebarItem
                        icon={<CogIcon />}
                        text="Account and Settings"
                      />
                      <SidebarItem
                        icon={<ArrowLeftStartOnRectangleIcon />}
                        text="Log out"
                        onClick={onLogout}
                      />
                    </SidebarSection>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>
    </aside>
  );
}

export { Sidebar };
