import { Menu, Transition } from '@headlessui/react';
import { ChatDots } from '../Icons';
import { Fragment } from 'react';

function ChatNavbar() {
  return (
    <div className="flex items-center justify-between pl-[11px] pr-4 py-[11px] border-b border-[#E5E8EE]">
      <div className="flex items-center gap-5">
        <img
          src="https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=2662&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
          alt="PP"
          className="w-9 h-9 rounded-full object-cover"
        />
        <h1 className="text-passiveLinkColor font-medium leading-5 text-lg -tracking-[0.02em]">
          Peter Thiel
        </h1>
      </div>
      <Menu as="div" className="relative inline-block">
        <Menu.Button className="px-2 py-[15px] border border-[#E5E8EE] rounded-md">
          <ChatDots />
        </Menu.Button>
        <Transition
          as={Fragment}
          enter="transition ease-out duration-100"
          enterFrom="transform opacity-0 scale-95"
          enterTo="transform opacity-100 scale-100"
          leave="transition ease-in duration-75"
          leaveFrom="transform opacity-100 scale-100"
          leaveTo="transform opacity-0 scale-95"
        >
          <Menu.Items className="absolute right-0 mt-2 w-44 origin-top-right divide-y divide-[#E5E8EE] rounded-md bg-white shadow-[0_0_24px_0_rgba(136,136,136,0.25)] ring-1 ring-black/5 focus:outline-none overflow-hidden">
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-violet-500 text-white' : 'text-gray-900'
                  } group flex w-full items-center px-5 pt-[13px] pb-[11px] text-sm leading-[18px] text-passiveLinkColor`}
                >
                  Delete Chat
                </button>
              )}
            </Menu.Item>
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-violet-500 text-white' : 'text-gray-900'
                  } group flex w-full items-center px-5 pt-[13px] pb-[11px] text-sm leading-[18px] text-passiveLinkColor`}
                >
                  Archive
                </button>
              )}
            </Menu.Item>
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-violet-500 text-white' : 'text-gray-900'
                  } group flex w-full items-center px-5 pt-[13px] pb-[11px] text-sm leading-[18px] text-passiveLinkColor`}
                >
                  Report User
                </button>
              )}
            </Menu.Item>
          </Menu.Items>
        </Transition>
      </Menu>
    </div>
  );
}

export { ChatNavbar };
