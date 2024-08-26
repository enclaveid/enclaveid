import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Fragment } from 'react/jsx-runtime';
import { Button } from './atoms/Button';
import { MarkIcon } from './atoms/Icons';

interface WarningModalProps {
  isOpen: boolean;
  closeModal: () => void;
  title: string;
  description: string;
  onConfirm: () => void;
}

export function WarningModal({
  isOpen,
  closeModal,
  title,
  description,
  onConfirm,
}: WarningModalProps) {
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
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-[403px] transform overflow-hidden rounded-xl bg-white px-11 pt-5 pb-7 text-left align-middle shadow-xl transition-all relative">
                <Dialog.Title
                  as="h3"
                  className="text-lg font-medium leading-[21px] text-passiveLinkColor text-center"
                >
                  {title}
                </Dialog.Title>
                <button onClick={closeModal} className="absolute right-4 top-5">
                  <XMarkIcon className="w-3 h-3 text-passiveLinkColor" />
                </button>

                <div className="flex flex-col gap-6 mt-6">
                  <div className="py-[18px] bg-[#A62F2F]/10 rounded-xl flex flex-col gap-5 px-4 items-center justify-center">
                    <MarkIcon />
                    <p className="text-[#A62F2F] text-sm text-center">
                      {description}
                    </p>
                  </div>
                  <div className="flex flex-col gap-4">
                    <Button
                      label="Confirm"
                      variant="error"
                      onClick={onConfirm}
                    />
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
