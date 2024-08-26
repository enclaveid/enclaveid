import { DiscordIcon, GithubIcon } from '../atoms/Icons';
import { Logo } from '../atoms/Logo';

function LandingFooter() {
  return (
    <footer className="lg:py-20 md:py-12 py-10  bg-[#297D69]">
      <div className="landing-container">
        <div className="flex flex-col md:gap-10 gap-6 lg:gap-14">
          {/* <div className="flex xl:items-center justify-between xl:flex-row flex-col xl:gap-0 gap-10">
            <div className="max-w-[632px] flex flex-col md:gap-5 gap-4 lg:gap-6">
              <h1 className="md:text-[32px] text-2xl md:leading-5 font-medium md:tracking-[-0.02em] text-white">
                Discover what your data says about you
              </h1>
              <p className="text-[#E3F1ED] md:tracking-[-0.02em] md:leading-6 md:text-lg">
                Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                Maecenas in neque vel diam consequat feugiat.{' '}
              </p>
            </div>
            <div className="flex md:flex-row flex-col md:items-center gap-2">
              <Link to="/signup">
                <button className="py-3.5 w-[168px] flex items-center justify-center text-center bg-greenBg rounded-full text-white tracking-[-0.02em] leading-3 text-sm">
                  Sign Up
                </button>
              </Link>
              <Link to="/login">
                <button className="py-3.5 w-[168px] flex items-center justify-center text-center bg-transparent rounded-full text-white tracking-[-0.02em] leading-3 text-sm outline outline-1 outline-[#E5E8EE]">
                  Login
                </button>
              </Link>
            </div>
          </div> */}
          <div className="lg:pt-10 md:pt-8 pt-6 sm:border-t border-[#51A38F]">
            <div className="flex lg:flex-row flex-col lg:gap-0 gap-10 lg:items-center justify-between">
              <div className="flex items-center gap-10">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10">
                    <Logo noText={true} />
                  </div>
                  <h6 className="text-white text-[32px] leading-[37px] tracking-[-0.02em]">
                    Enclave<span className="font-semibold">ID</span>
                  </h6>
                </div>
                <div className="text-white flex items-center gap-4">
                  <a
                    href="https://discord.gg/BftCHbV4TW"
                    target="_blank"
                    rel="noreferrer"
                  >
                    <DiscordIcon />
                  </a>
                  <a
                    href="https://github.com/enclaveid/enclaveid"
                    target="_blank"
                    rel="noreferrer"
                  >
                    <GithubIcon />
                  </a>
                </div>
              </div>
              <span className="text-[#DFE1E8] text-lg leading-7">
                ©2023 EnclaveID · All rights reserved.
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

export { LandingFooter };
