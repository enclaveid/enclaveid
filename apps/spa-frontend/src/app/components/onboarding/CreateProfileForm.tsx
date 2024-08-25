import { useNavigate } from 'react-router-dom';
import { Button } from '../Button';
import { Input } from '../Input';
import { backgroundPattern } from '../../utils/backgroundPattern';
import { LocationPicker } from '../LocationPicker';
import { OptionPicker } from '../OptionPicker';
import { Gender } from '@prisma/client';
import { getIdenticon } from '../../utils/ui/identicons';
import { useEffect, useState } from 'react';
import { LoadingCheckmark } from '../LoadingCheckmark';
import { trpc } from '../../utils/trpc';

function FormLabel({ label }: { label: string }) {
  return (
    <label className="text-[#6C7A8A] text-sm font-medium leading-[19.6px] block">
      {label}
    </label>
  );
}

export function CreateProfileForm() {
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState('');
  const usernameAvailableQuery = trpc.private.isDisplayNameAvailable.useQuery(
    {
      displayName,
    },
    {
      enabled: false, // Disable automatic query execution
    },
  );

  // Refetch the query if the displayName changes with a debounce of 500ms
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      usernameAvailableQuery.refetch();
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [displayName, usernameAvailableQuery]);

  return (
    <section
      className="min-h-screen onboarding-gradient flex items-center justify-center"
      style={{ ...backgroundPattern }}
    >
      <div className="flex flex-col gap-6 items-center">
        <h1 className="text-passiveLinkColor tracking-[0.02em] leading-[42px] font-medium text-4xl">
          Create a profile
        </h1>
        <div className="bg-white px-9 pt-8 pb-5 border border-[#E5E8EE] rounded-xl max-w-[478px] w-full flex flex-col">
          <h1 className="leading-[22px] text-passiveLinkColor">
            Now, let’s get some basic information to build your profile.
          </h1>
          <div className="flex flex-col gap-3.5 mt-5">
            <FormLabel label="Identicon and username" />
            <div className="flex items-center gap-3.5">
              <img
                src={getIdenticon(displayName)}
                alt=""
                className="w-[50px] h-[50px] rounded-full"
              />
              <Input
                placeholder="Minimum 4 characters"
                type="text"
                id="username"
                fullWidth
                style={{
                  backgroundColor: 'transparent',
                }}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
              <LoadingCheckmark booleanQuery={usernameAvailableQuery} />
            </div>

            <FormLabel label="Gender" />
            <OptionPicker
              options={Object.values(Gender)}
              label="Gender"
              onChange={(option) => console.log(option)}
            />
            <FormLabel label="Location" />
            <LocationPicker />
          </div>
          <div className="mt-5">
            <Button
              label="Sign Up"
              fullWidth
              className="mt-5"
              onClick={() => navigate('/onboarding/purposeSelection')}
            />
          </div>
          <div className="mt-5">
            <Button
              label="Go back"
              variant="secondary"
              fullWidth
              onClick={() => navigate('/onboarding')}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
