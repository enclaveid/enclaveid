import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trpc } from '../utils/trpc';
import { Button } from '../components/atoms/Button';
import { LoadingPage } from './LoadingPage';
import { WarningModal } from '../components/WarningModal';

type Setting = {
  label: string;
  key: string;
  type: 'toggle' | 'action';
};

const SETTINGS: Setting[] = [
  {
    label: 'Enable matching with other users',
    key: 'matchingEnabled',
    type: 'toggle',
  },
  {
    label: 'Match with others over sensitive topics',
    key: 'sensitiveMatchingEnabled',
    type: 'toggle',
  },
  //{ label: 'Download my data', key: 'downloadData', type: 'action' },
  {
    label: 'Delete my account and all of my data',
    key: 'deleteAccount',
    type: 'action',
  },
];

const ToggleButton: React.FC<{
  value: boolean;
  onChange: (value: boolean) => void;
}> = ({ value, onChange }) => (
  <div className="flex items-center">
    {['Yes', 'No'].map((option) => (
      <label key={option} className="flex items-center mr-4">
        <input
          type="radio"
          checked={value === (option === 'Yes')}
          onChange={() => onChange(option === 'Yes')}
          className="hidden"
        />
        <span
          className={`w-5 h-5 border-[0.77px] rounded-full flex items-center justify-center bg-[#F3F5F7] ${
            value === (option === 'Yes') ? 'border-greenBg' : 'border-[#B5BDBB]'
          }`}
        >
          {value === (option === 'Yes') && (
            <span className="w-2.5 h-2.5 bg-greenBg rounded-full"></span>
          )}
        </span>
        <span className="ml-2 text-passiveLinkColor">{option}</span>
      </label>
    ))}
  </div>
);

export function AccountSettings() {
  const navigate = useNavigate();
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [localSettings, setLocalSettings] = useState<Record<string, boolean>>(
    {},
  );

  const { data: serverSettings, isLoading } =
    trpc.private.getSettings.useQuery();
  const updateSettingMutation = trpc.private.updateSettings.useMutation();
  const downloadDataMutation = trpc.private.downloadData.useMutation();
  const deleteAccountMutation = trpc.private.deleteEverything.useMutation();

  useEffect(() => {
    if (serverSettings) {
      setLocalSettings(serverSettings);
    }
  }, [serverSettings]);

  const handleSettingChange = (key: string, value: boolean) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
    updateSettingMutation.mutate({ [key]: value });
  };

  const handleAction = (key: string) => {
    if (key === 'downloadData') {
      downloadDataMutation.mutate();
    } else if (key === 'deleteAccount') {
      setIsDeleteModalOpen(true);
    }
  };

  const handleDeleteAccount = () => {
    deleteAccountMutation.mutate(undefined, {
      onSuccess: () => navigate('/login'),
    });
  };

  if (isLoading) return <LoadingPage />;

  return (
    <div className="flex flex-col gap-7 px-6">
      <h1 className="text-passiveLinkColor text-[23px] leading-[27px] font-medium">
        Account and Settings
      </h1>
      <div className="flex flex-col gap-3">
        {SETTINGS.map((setting) => (
          <div
            key={setting.key}
            className="max-w-[538px] w-full flex items-center justify-between border border-[#E5E8EE] rounded-xl pl-5 pr-3.5 py-3.5"
          >
            <label className="leading-[18px] text-passiveLinkColor">
              {setting.label}
            </label>
            {setting.type === 'toggle' ? (
              <ToggleButton
                value={localSettings[setting.key]}
                onChange={(value) => handleSettingChange(setting.key, value)}
              />
            ) : (
              <Button
                variant="secondary"
                label={setting.key === 'deleteAccount' ? 'Delete' : 'Download'}
                onClick={() => handleAction(setting.key)}
              />
            )}
          </div>
        ))}
      </div>
      <WarningModal
        isOpen={isDeleteModalOpen}
        closeModal={() => setIsDeleteModalOpen(false)}
        title="Deleting Account"
        description="You're about to delete your entire account and profile. Your history will be erased and this action can't be undone."
        onConfirm={handleDeleteAccount}
      />
    </div>
  );
}
