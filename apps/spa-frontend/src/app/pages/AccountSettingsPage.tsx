import classNames from 'classnames';
import { useState } from 'react';
import { WarningModal } from '../components/WarningModal';
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

export function AccountSettings() {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const deleteEverythingMutation = trpc.private.deleteEverything.useMutation();

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
      <WarningModal
        closeModal={() => setIsOpen(false)}
        isOpen={isOpen}
        title="Deleting Account"
        description="You’re about to delete your entire account and profile. Your history will be erased and this action can’t be undone."
        onConfirm={() => {
          deleteEverythingMutation.mutate(null, {
            onSuccess: () => {
              navigate('/login');
            },
          });
        }}
      />
    </div>
  );
}
