import { useNavigate } from 'react-router-dom';
import { Button } from '../Button';
import { Input } from '../Input';
import { backgroundPattern } from '../../utils/backgroundPattern';
import { LocationPicker } from '../LocationPicker';
import { OptionPicker } from '../OptionPicker';

function CreateProfileForm() {
  const navigate = useNavigate();

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
            <Input
              label="Username"
              placeholder="discordusername"
              type="text"
              id="username"
              fullWidth
              style={{
                backgroundColor: 'transparent',
              }}
            />
            <Input
              label="Email"
              placeholder="yourdiscord@gmail.com"
              type="email"
              id="email"
              fullWidth
              required
              style={{
                backgroundColor: 'transparent',
              }}
            />
            <OptionPicker
              options={['Male', 'Female', 'Other']}
              label="Gender"
              onChange={(option) => console.log(option)}
            />
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

export { CreateProfileForm };
