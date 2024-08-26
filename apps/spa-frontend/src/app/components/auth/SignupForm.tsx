import { useNavigate } from 'react-router-dom';
import { Button } from '../atoms/Button';
import { Input } from '../atoms/Input';
import { backgroundPattern } from '../../utils/backgroundPattern';
import { LocationPicker } from '../atoms/LocationPicker';
import { OptionPicker } from '../atoms/OptionPicker';
import { Gender } from '@prisma/client';
import { getIdenticon } from '../../utils/ui/identicons';
import { useEffect, useState } from 'react';
import { LoadingCheckmark } from '../atoms/LoadingCheckmark';
import { Logo } from '../atoms/Logo';
import { useDisplayNameAvailable } from '../../hooks/useDisplayNameAvailable';
import { useEmailAvailable } from '../../hooks/useEmailAvailable';

function FormLabel({ label }: { label: string }) {
  return (
    <label className="text-[#6C7A8A] text-md font-medium leading-[19.6px] block">
      {label}
    </label>
  );
}

interface SignupFormData {
  displayName: string;
  gender: Gender;
  country: string;
  email: string;
  password: string;
}

export interface SignupFormProps {
  handleSubmit?: (formData: SignupFormData) => void;
}

export function SignupForm({ handleSubmit }: SignupFormProps) {
  const [formData, setFormData] = useState<SignupFormData>({
    displayName: '',
    gender: null,
    country: null,
    email: '',
    password: '',
  });

  const navigate = useNavigate();
  const isDisplayNameAvailable = useDisplayNameAvailable(formData.displayName);
  const isEmailAvailable = useEmailAvailable(formData.email);

  const isFormValid =
    Object.values(formData).every(Boolean) &&
    isDisplayNameAvailable === 'available' &&
    isEmailAvailable === 'available';

  // When the email is changed, set the displayName to the email without the @
  useEffect(() => {
    setFormData((f) => ({
      ...f,
      displayName: f.email.split('@')[0].substring(0, 16),
    }));
  }, [formData.email]);

  return (
    <section
      className="min-h-screen onboarding-gradient flex items-center justify-center h-full"
      style={{ ...backgroundPattern }}
    >
      <div className="flex flex-col gap-6 items-center">
        <Logo />
        <div className="bg-white p-5 border border-[#E5E8EE] rounded-xl max-w-[478px] w-full flex flex-col">
          {/* <h1 className="leading-[22px] text-passiveLinkColor">
            Now, let’s get some basic information to build your profile.
          </h1> */}
          <div className="flex flex-col gap-3.5">
            <FormLabel label="Email and Password" />

            <div className="flex flex-row gap-3.5">
              <Input
                placeholder="yourmail@gmail.com"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData((f) => ({ ...f, email: e.target.value }))
                }
                fullWidth
              />
              <LoadingCheckmark status={isEmailAvailable} />
            </div>
            <p className="text-sm text-passiveLinkColor">
              Your email is only visible to you.
            </p>
            <Input
              placeholder="**********"
              type="password"
              fullWidth
              value={formData.password}
              onChange={(e) =>
                setFormData((f) => ({ ...f, password: e.target.value }))
              }
            />
            <FormLabel label="Identicon and Display Name" />
            <div className="flex items-center gap-3.5">
              <img
                src={getIdenticon(formData.displayName)}
                alt=""
                className="w-[50px] h-[50px] rounded-full"
              />
              <Input
                placeholder="Minimum 4 characters"
                type="text"
                fullWidth
                value={formData.displayName}
                onChange={(e) =>
                  setFormData((f) => ({ ...f, displayName: e.target.value }))
                }
                maxLength={16}
              />
              <LoadingCheckmark status={isDisplayNameAvailable} />
            </div>
            <p className="text-sm text-passiveLinkColor">
              Your identicon and display name are visible to everyone.
            </p>

            <FormLabel label="Location" />
            <LocationPicker
              onChange={(option) =>
                setFormData((f) => ({ ...f, country: option.value }))
              }
            />
            <FormLabel label="Gender" />
            <OptionPicker
              options={Object.values(Gender)}
              label="Gender"
              onChange={(option) =>
                setFormData((f) => ({ ...f, gender: option }))
              }
            />
          </div>
          {isFormValid && (
            <Button
              label="Sign Up"
              fullWidth
              className="mt-5"
              onClick={() => handleSubmit(formData)}
            />
          )}
          <div className="mt-5">
            <Button
              label="Already have an account? Log in"
              variant="secondary"
              fullWidth
              onClick={() => navigate('/login')}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
