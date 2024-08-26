import { Link } from 'react-router-dom';
import { Logo } from '../atoms/Logo';
import { DiscordIcon, GithubIcon } from '../atoms/Icons';
import { ChevronRightIcon } from '@heroicons/react/24/outline';

function LandingNavbar() {
  return (
    <header className="bg-[#32433F] sm:bg-transparent py-6 sm:absolute sm:top-0 z-50 w-full">
      <nav className="landing-container">
        <div className="flex items-center justify-between xl:pl-10 xl:pr-12">
          <Logo isSmall={true} />
          {/* <div className="lg:flex items-center gap-6 hidden">
            <button className="px-5 py-2.5 leading-3 text-lg font-medium tracking-[-0.02em] text-greenBg bg-greenBg/10 rounded-full">
              Home
            </button>
            <button className="text-lg font-medium tracking-[-0.02em] leading-3 text-[#B5BBBB]">
              About
            </button>
          </div> */}
          <div className="flex items-center gap-4">
            <a
              href="https://discord.gg/BftCHbV4TW"
              target="_blank"
              rel="noreferrer"
              className="text-greenBg"
            >
              <DiscordIcon />
            </a>
            <a
              href="https://github.com/enclaveid/enclaveid"
              target="_blank"
              rel="noreferrer"
              className="text-greenBg"
            >
              <GithubIcon />
            </a>
            <Link to="/login" className="lg:block hidden">
              <button className="w-[109px] h-10 flex items-center justify-center border border-greenBg text-greenBg rounded-lg text-sm font-medium leading-3">
                Log In
              </button>
            </Link>
            <Link to="/signup" className="lg:block hidden">
              <button className="w-[109px] h-10 flex items-center justify-center gap-1 bg-greenBg rounded-lg">
                <span className="text-white text-sm font-medium leading-3">
                  Sign Up
                </span>
                <ChevronRightIcon className="w-4 h-4 text-white" />
              </button>
            </Link>
          </div>
        </div>
      </nav>
    </header>
  );
}

export { LandingNavbar };
