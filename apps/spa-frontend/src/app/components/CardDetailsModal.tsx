import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Fragment } from 'react';

export function CardDetailsModal({
  isOpen,
  closeModal,
  title,
  description,
}: {
  isOpen: boolean;
  closeModal: () => void;
  title: string;
  description: string;
}) {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={closeModal}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex items-center justify-center p-4 text-center h-full">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-[1112px] h-full max-h-[752px] transform overflow-hidden rounded-xl bg-white px-[17px] pt-5 pb-6 text-left align-middle shadow-xl transition-all relative flex flex-col">
                <Dialog.Title
                  as="h3"
                  className="text-lg font-medium leading-[21px] text-passiveLinkColor"
                >
                  {title}
                </Dialog.Title>
                <Dialog.Description className="m-3 text-passiveLinkColor bg-white rounded-xl px-3.5 pt-5 pb-4 border border-[#E5E8EE] h-full flex flex-col justify-between">
                  {description}
                </Dialog.Description>
                <button onClick={closeModal} className="absolute right-4 top-5">
                  <XMarkIcon className="w-5 h-5 stroke-[3px] text-passiveLinkColor" />
                </button>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
