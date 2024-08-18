import { Button } from './Button';
import {
  BrainIcon,
  FacebookIconU,
  GoogleIconU,
  OpenAiIconU,
  UserIcon,
} from './Icons';
import { Link } from './Link';

const data = [
  {
    icon: <UserIcon />,
    description:
      'We save your profile information as credentials and if you enable social features',
  },
  {
    icon: <BrainIcon />,
    description:
      'We save your personality traits to help run our algorithm and for features such as social journeys',
  },
  {
    icon: <GoogleIconU />,
    description:
      'We access your searches to provide you with journey maps and help our algorithm assess your personality traits',
  },
  {
    icon: <FacebookIconU />,
    description:
      'We access your messages to help the algorithm assess your personality traits',
  },
  {
    icon: <OpenAiIconU />,
    description:
      'We access your conversations with ChatGPT to help the algorithm assess your personality traits',
  },
];

function CreateProfile() {
  return (
    <section className="min-h-screen onboarding-gradient flex items-center justify-center">
      <div className="flex flex-col gap-6 items-center">
        <h1 className="text-passiveLinkColor tracking-[0.02em] leading-[42px] font-medium text-4xl">
          Create a profile
        </h1>
        <div className="bg-white px-9 pt-8 pb-5 border border-[#E5E8EE] rounded-xl max-w-[597px] w-full flex flex-col">
          <h1 className="leading-[22px] text-passiveLinkColor">
            By connecting your account, you agree to provide us with the
            following data:
          </h1>
          <div className="flex flex-col gap-1.5 mt-[17px]">
            {data.map((item, index) => {
              return (
                <div
                  key={index}
                  className="flex items-center gap-3.5 border border-[#E5E8EE] rounded-md px-2.5 py-3"
                >
                  <span className="shrink-0">{item.icon}</span>
                  <span className="text-passiveLinkColor text-sm leading-5">
                    {item.description}
                  </span>
                </div>
              );
            })}
          </div>
          <p className="text-sm leading-5 text-passiveLinkColor mt-5">
            Our app is completely{' '}
            <a href="#" className="text-greenBg underline decoration-greenBg">
              open source{' '}
            </a>{' '}
            and built using Zero Trust Infrastructure which assumes that no one,
            inside or outside the network, is trusted by default. Every access
            request is verified continuously like a bouncer checking IDs at
            every door, every time. This assures the safety and privacy of your
            data.{' '}
          </p>
          <div className="mt-5 flex flex-col gap-3">
            <Button label="Confirm" />
            <Link>I want to learn more</Link>
          </div>
        </div>
      </div>
    </section>
  );
}

export { CreateProfile };
