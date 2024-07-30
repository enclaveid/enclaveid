import classNames from 'classnames';
import { useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Button } from '../components/Button';
import { MarkIcon } from '../components/Icons';
import { useNavigate } from 'react-router-dom';
import { trpc } from '../utils/trpc';

interface SettingOption {
  label: string;
  value: boolean;
}

interface AccountSettings {
  [key: string]: SettingOption[] | { deleteAccount?: string; logOut?: string };
}

interface SectionTabProps {
  title: string;
  settings?: SettingOption[];
  moreOptions?: { deleteAccount?: string; logOut?: string };
  openModal?: () => void;
}

interface RadioGroupProps {
  name: string;
  options: { label: string; value: boolean }[];
  selectedValue: boolean;
  onChange: (value: boolean) => void;
}

interface ModalProps {
  isOpen: boolean;
  closeModal: () => void;
}

const accountSettings: AccountSettings = {
  'Social features': [
    {
      label: 'Enable matching with other users',
      value: true,
    },
    {
      label: 'Match with others over sensitive topics',
      value: true,
    },
  ],
  'Danger zone': {
    deleteAccount: 'Delete my account and all of my data',
  },
};

const RadioGroup = ({
  name,
  options,
  selectedValue,
  onChange,
}: RadioGroupProps) => {
  return (
    <div className="flex items-center">
      {options.map((option, index) => (
        <label key={index} className="flex items-center mr-4">
          <input
            type="radio"
            name={name}
            value={option.value.toString()}
            checked={selectedValue === option.value}
            onChange={() => onChange(option.value)}
            className="hidden"
          />
          <span
            className={classNames(
              'w-5 h-5 border-[0.77px] rounded-full flex items-center justify-center bg-[#F3F5F7]',
              selectedValue === option.value
                ? 'border-greenBg'
                : 'border-[#B5BDBB]',
            )}
          >
            {selectedValue === option.value && (
              <span className="w-2.5 h-2.5 bg-greenBg rounded-full"></span>
            )}
          </span>
          <span className="ml-2 text-passiveLinkColor">{option.label}</span>
        </label>
      ))}
    </div>
  );
};

const SectionTab = ({
  title,
  settings,
  moreOptions,
  openModal,
}: SectionTabProps) => {
  const [selectedValues, setSelectedValues] = useState<{
    [key: string]: boolean;
  }>({});

  const handleChange = (label: string, value: boolean) => {
    setSelectedValues({ ...selectedValues, [label]: value });
  };
  return (
    <section className="flex flex-col gap-3.5">
      <h1 className="leading-4 text-sm text-passiveLinkColor pb-[11px] border-b border-[#E5E8EE]">
        {title}
      </h1>
      <div className="flex flex-col gap-3">
        {settings &&
          settings.map((setting, index) => (
            <div
              key={index}
              className="max-w-[538px] w-full flex items-center justify-between border border-[#E5E8EE] rounded-xl pl-5 pr-3.5 py-3.5"
            >
              <label className="leading-[18px] text-passiveLinkColor">
                {setting.label}
              </label>
              <RadioGroup
                name={setting.label}
                options={[
                  { label: 'Yes', value: true },
                  { label: 'No', value: false },
                ]}
                selectedValue={selectedValues[setting.label] ?? setting.value}
                onChange={(value) => handleChange(setting.label, value)}
              />
            </div>
          ))}
        {moreOptions && (
          <>
            {moreOptions.deleteAccount && (
              <div className="max-w-[538px] w-full flex items-center justify-between border border-[#E5E8EE] rounded-xl pl-5 pr-3.5 py-3.5">
                <label className="leading-[18px] text-passiveLinkColor">
                  {moreOptions.deleteAccount}
                </label>
                <button
                  className="text-[#A62F2F] underline decoration-[#A62F2F] leading-[18px]"
                  onClick={openModal}
                >
                  Delete
                </button>
              </div>
            )}
            {moreOptions.logOut && (
              <div className="max-w-[538px] w-full flex items-center justify-between border border-[#E5E8EE] rounded-xl pl-5 pr-3.5 py-3.5">
                <label className="leading-[18px] text-passiveLinkColor">
                  {moreOptions.logOut}
                </label>
                <button className="text-greenBg underline decoration-greenBg underline-offset-2 leading-[18px]">
                  Log Out
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
};

const DeleteModal = ({ isOpen, closeModal }: ModalProps) => {
  const navigate = useNavigate();

  const deleteEverythingMutation = trpc.private.deleteEverything.useMutation();

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
                  Deleting Account
                </Dialog.Title>
                <button onClick={closeModal} className="absolute right-4 top-5">
                  <XMarkIcon className="w-3 h-3 text-passiveLinkColor" />
                </button>

                <div className="flex flex-col gap-6 mt-6">
                  <div className="py-[18px] bg-[#A62F2F]/10 rounded-xl flex flex-col gap-5 px-4 items-center justify-center">
                    <MarkIcon />
                    <p className="text-[#A62F2F] text-sm text-center">
                      You’re about to delete your entire account and profile.
                      Your history will be erased and this action can’t be
                      reversed.
                    </p>
                  </div>
                  <div className="flex flex-col gap-4">
                    {/* <input
                      type="text"
                      className="border border-[#D2DAE8] rounded-lg py-[11px] pl-[11px] pr-[15px] text-passiveLinkColor leading-[18px]"
                      placeholder="Enter your password to confirm"
                    /> */}
                    <Button
                      label="Confirm and Delete Account"
                      variant="error"
                      onClick={() =>
                        deleteEverythingMutation.mutate(null, {
                          onSuccess: () => {
                            navigate('/login');
                          },
                        })
                      }
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
};

export function AccountSettings() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex flex-col gap-7 px-6">
      <h1 className="text-passiveLinkColor text-[23px] leading-[27px] font-medium">
        Account and Settings
      </h1>
      <div className="flex flex-col gap-[74px]">
        {Object.keys(accountSettings).map((key) => {
          const settings = accountSettings[key];
          if (Array.isArray(settings)) {
            return (
              <SectionTab
                key={key}
                title={key.charAt(0).toUpperCase() + key.slice(1)}
                settings={settings}
                openModal={() => setIsOpen(true)}
              />
            );
          } else {
            return (
              <SectionTab
                key={key}
                title={key.charAt(0).toUpperCase() + key.slice(1)}
                moreOptions={settings}
                openModal={() => setIsOpen(true)}
              />
            );
          }
        })}
      </div>
      <DeleteModal closeModal={() => setIsOpen(false)} isOpen={isOpen} />
    </div>
  );
}
