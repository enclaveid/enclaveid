import DiscordIcon from '~icons/mdi/discord.tsx';
import GitHubIcon from '~icons/mdi/github.tsx';
import Image from 'next/image';
import { Logo } from '../../../../libs/ui/src/logo';
import LandingVideo from './components/landing-video';
import { Button } from '@enclaveid/ui/button';
import Link from 'next/link';

export default function Index() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-800">
      <Header />
      <main className="flex-grow">
        <Hero />
        <PrivacySection />
      </main>
      <Footer />
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-50 bg-offwhite">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Company Name */}
          <div className="flex items-center gap-1 font-bold text-2xl text-content-primary">
            <Logo />
            EnclaveID
          </div>

          {/* Navigation / Social Icons */}
          <nav className="flex gap-4 items-center">
            <a
              href="https://discord.gg/3BHPkHDs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-content-secondary hover:text-content-primary"
            >
              <DiscordIcon className="w-6 h-6" />
            </a>
            <a
              href="https://github.com/enclaveid/enclaveid"
              target="_blank"
              rel="noopener noreferrer"
              className="text-content-secondary hover:text-content-primary"
            >
              <GitHubIcon className="w-6 h-6" />
            </a>

            <Link href="/dashboard/home">
              <Button size="sm">Sign In</Button>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="bg-offwhite pt-12 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col md:flex-row items-center gap-12">
          <div className="w-full md:w-1/2 max-w-2xl md:mt-[-100px]">
            <h1 className="text-3xl md:text-5xl font-bold mb-4">
              Get LLMs to know you
            </h1>
            <p className="text-lg md:text-xl text-gray-600 mb-6">
              EnclaveID builds an easily queryable, rich causal graph of your
              life and your projects so you can stop re-explaining yourself
              every time and focus on your goals.
            </p>
            <Link href="/dashboard/home">
              <Button size="lg">Get Started</Button>
            </Link>
          </div>

          {/* Video Container */}
          <div className="w-full md:w-1/2 mb-8 md:mb-0">
            <LandingVideo />
            <div className="relative text-center text-sm text-gray-400 mt-4">
              Click / touch to pause and unpause
            </div>
          </div>
        </div>
      </div>

      <div
        className="absolute bottom-0 left-0 right-0 md:h-[500px] h-[250px] bg-white"
        style={{
          clipPath: 'polygon(0 100%, 100% 100%, 100% 50%, 0 75%)',
        }}
      />
    </section>
  );
}

function PrivacySection() {
  return (
    <section className="bg-white py-16 sm:py-20 lg:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 lg:gap-16">
          {/* Left column */}
          <div className="flex flex-col justify-center gap-8 md:gap-16">
            <div className="flex flex-col">
              <div className="flex flex-row md:flex-col text-brand">
                <h2 className="text-3xl md:text-5xl font-bold leading-snug mr-2 opacity-50">
                  Your data,
                </h2>
                <h2 className="text-3xl md:text-5xl font-bold leading-snug">
                  Your rules
                </h2>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-1 gap-2 md:gap-8 place-items-center md:place-items-start">
              <div className="flex items-center w-32 md:w-40 lg:w-48">
                <Image
                  src="/nvtrust.png"
                  alt="NVIDIA nvtrust logo"
                  width={160}
                  height={160}
                  className="w-full h-auto"
                />
              </div>
              <div className="flex items-center w-32 md:w-40 lg:w-48">
                <Image
                  src="/coco.png"
                  alt="Confidential Containers"
                  width={160}
                  height={160}
                  className="w-full h-auto"
                />
              </div>
              <div className="flex items-center w-32 md:w-40 lg:w-48 col-span-2 md:col-span-1 justify-self-center md:justify-self-start">
                <Image
                  src="/amd.png"
                  alt="AMD SEV-SNP"
                  width={160}
                  height={160}
                  className="w-full h-auto"
                />
              </div>
            </div>
          </div>

          {/* Right column: Info blocks */}
          <div className="space-y-8">
            {/* Zero Trust */}
            <div>
              <h3 className="text-xl font-bold text-brand mb-2">
                Zero Trust Infrastructure
              </h3>
              <p className="text-content-secondary">
                EnclaveID runs on AMD SEV-SNP capable hardware – hence “enclave”
                in the name – which guarantees that your data is inaccessible by
                any other software or human (except you), even by the
                infrastructure provider!
              </p>
            </div>

            {/* Open Source */}
            <div>
              <h3 className="text-xl font-bold text-brand mb-2">
                100% Open Source
              </h3>
              <p className="text-gray-700">
                Every single component of EnclaveID is publicly available on
                GitHub and the build pipeline is fully reproducible. Thanks to
                remote
                <em> attestation</em>, this means that you can trust that
                whatever is in the code is what is running in our Kubernetes
                cluster, much like an Ethereum smart contract.
              </p>
            </div>

            {/* Community Owned */}
            <div>
              <h3 className="text-xl font-bold text-brand mb-2">
                Community Owned
              </h3>
              <p className="text-gray-700">
                EnclaveID is a community-owned project with the goal of
                empowering individuals for a flourishing democratic society. Our
                code is a reflection of the will of such individuals, so
                contributions and feedback are strongly encouraged!
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-offwhite text-text">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="col-span-1">
            <h3 className="text-gray-900 font-bold text-lg mb-4">EnclaveID</h3>
            <p className="text-sm text-gray-900">Get LLMs to know you</p>
          </div>

          {/* Quick Links */}
          {/* <div className="col-span-1">
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Documentation
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  About Us
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div> */}

          {/* Social Links */}
          {/* <div className="col-span-1">
            <h4 className="text-gray-900 font-semibold mb-4">Connect</h4>
            <div className="flex gap-4">
              <a
                href="https://discord.gg/your-discord"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-900 hover:text-gray-700"
              >
                <DiscordIcon className="w-6 h-6" />
              </a>
              <a
                href="https://github.com/your-github"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-900 hover:text-gray-700"
              >
                <GitHubIcon className="w-6 h-6" />
              </a>
            </div>
          </div> */}
        </div>

        {/* Copyright */}
        <div className="border-t border-footer-border mt-8 pt-8 text-sm text-gray-900">
          © {new Date().getFullYear()} EnclaveID. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
