import { Logo } from '../atoms/Logo';

function LandingConnections() {
  return (
    <section className="max-w-[1440px] px-6 mx-auto py-10 2xl:pt-[154px] 2xl:pb-[160px]">
      <div className="rounded-3xl overflow-hidden flex lg:flex-row flex-col w-full">
        <div className="bg-greenBg py-8 md:py-20 lg:py-[160px] flex flex-col md:pl-14 xl:pl-[88px] md:pr-14 px-6 md:gap-12 gap-10 lg:gap-16">
          <div className="flex flex-col gap-6 xl:max-w-[422px]">
            <div className="py-2 pl-2 pr-4 bg-white/10 max-w-max rounded-full flex items-center gap-1.5">
              <div className="w-6 h-6 rounded-full border border-white overflow-hidden ">
                <Logo noText={true} />
              </div>
              <h6 className="text-white text-[19px] leading-[22px] tracking-[-0.02em]">
                <span className="font-semibold">New!</span>
              </h6>
            </div>
            <div className="flex flex-col">
              <h1 className="md:text-[54px] md:leading-[48px] text-4xl md:tracking-[-0.04em] text-white">
                Deep and lasting
              </h1>
              <h1 className="md:text-[70px] md:leading-[62px] text-5xl font-medium text-white md:tracking-[-0.04em]">
                connections
              </h1>
            </div>
            <p className="text-white/80 md:tracking-[-0.02em] md:text-base text-sm">
              Early friendships form in the simplicity of shared beginnings, but
              as we age our interests, struggles, and values become more complex
              and defined. EnclaveID lets you effortlessly leverage this
              uniqueness to connect with others, with full control on how much
              you share.
            </p>
          </div>
          <div>
            <button className="text-greenBg bg-white rounded-lg px-[38.5px] py-[18.5px] leading-3 font-medium tracking-[-0.02em]">
              Try It Out
            </button>
          </div>
        </div>
        <div className="bg-[#2F9C82] flex flex-1 items-end justify-end min-w-[600px]">
          <img
            src="/social.png"
            alt="Connection"
            className="outline-2 outline-[#E5EAE8] md:rounded-tl-2xl overflow-hidden"
          />
        </div>
      </div>
    </section>
  );
}

export { LandingConnections };
