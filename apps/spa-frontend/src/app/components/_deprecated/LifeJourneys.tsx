import { Dialog, Tab, Transition } from '@headlessui/react';
import { NonLatentCard } from './NonLatentCard';
import { Stepper } from './Stepper';
import { Button } from '../atoms/Button';
import { Fragment } from 'react/jsx-runtime';
import { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const data = [
  {
    title: 'Repairing the e-shifter on your VanMoof S3',
    description:
      'The VanMoof e-shifter is known to cause problems. Have you considered switching to an analog shifter?',
    content: 'Card Content1',
  },
  {
    title: 'Repairing the e-shifter on your VanMoof S3',
    description:
      'Your Oura readings are normal. Your chest pain while running is likely due to GERD rather than heart disease.',
    content: 'Card Content2',
  },
  {
    title: 'Unsuccessful dating streak',
    description:
      'Seems like your past few dates haven’t been going as expected. There are some common traits that perhaps you should avoid.',
    content: 'Card Content3',
  },
];
const steps = [
  { label: 'Step one on the journey' },
  { label: 'Step two on the journey' },
  { label: 'Step three on the journey' },
];

function LifeJourneys() {
  const [isOpen, setIsOpen] = useState(false);

  function closeModal() {
    setIsOpen(false);
  }

  function openModal() {
    setIsOpen(true);
  }

  return (
    <div className="flex flex-col gap-6 px-6">
      <h1 className="pt-[21px] pb-[13px] leading-[21.11px] text-lg text-passiveLinkColor text-center border-b w-full border-[#E5E8EE]">
        Life Journeys
      </h1>
      <Tab.Group>
        <div className="flex xl:flex-row flex-col-reverse gap-[18px] w-full">
          <Tab.List className="flex flex-col gap-4 shrink-0">
            {data.map((card, index) => (
              <Tab key={index} className="w-full focus-visible:outline-none">
                {({ selected }) => (
                  <NonLatentCard {...card} isViewed={selected} />
                )}
              </Tab>
            ))}
          </Tab.List>
          <Tab.Panels className="w-full">
            {data.map((_, index) => (
              <Tab.Panel key={index} className="size-full">
                <div className="border border-[#E5E8EE] bg-[#F3F5F7] pt-5 pb-3.5 px-2.5 rounded-xl flex flex-col gap-[60px] h-full">
                  <Stepper steps={steps} />
                  <div className="text-passiveLinkColor bg-white rounded-xl px-3.5 pt-5 pb-4 border border-[#E5E8EE] h-full flex flex-col justify-between">
                    <p className="text-passiveLinkColor leading-[22px]">
                      Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                      Pellentesque leo lorem, pellentesque at rutrum sit amet,
                      dignissim at ex. Mauris suscipit est quis sem rhoncus
                      aliquam vel et erat. Sed eget commodo ipsum, maximus
                      facilisis diam. Vestibulum aliquet elit quam, eget viverra
                      erat pretium vitae. <br /> <br /> Nunc consequat tempor
                      velit ac suscipit. Suspendisse potenti. Nulla tincidunt
                      elit arcu, nec rhoncus ipsum fermentum at. Quisque
                      vehicula viverra tellus, ac finibus felis porttitor a.
                      Donec condimentum sem laoreet eros malesuada, non
                      hendrerit enim consectetur. Nulla in lacus non odio
                      interdum feugiat vitae in libero.
                    </p>
                    <div className="flex items-center justify-center">
                      <Button label="Expand" size="large" onClick={openModal} />
                    </div>
                  </div>
                  <Transition appear show={isOpen} as={Fragment}>
                    <Dialog
                      as="div"
                      className="relative z-10"
                      onClose={closeModal}
                    >
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
                                Expanded Path - Repairing the e-shifter on your
                                VanMoof S3
                              </Dialog.Title>
                              <button
                                onClick={closeModal}
                                className="absolute right-4 top-5"
                              >
                                <XMarkIcon className="w-5 h-5 stroke-[3px] text-passiveLinkColor" />
                              </button>

                              <div className="mt-6 border-[1.28px] border-[#E4E4E7] rounded-lg h-full"></div>
                            </Dialog.Panel>
                          </Transition.Child>
                        </div>
                      </div>
                    </Dialog>
                  </Transition>
                </div>
              </Tab.Panel>
            ))}
          </Tab.Panels>
        </div>
      </Tab.Group>
    </div>
  );
}

export { LifeJourneys };
