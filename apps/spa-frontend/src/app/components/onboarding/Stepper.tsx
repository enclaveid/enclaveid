import React from 'react';

interface Step {
  label: string;
}

interface StepperProps {
  steps: Step[];
}
function Stepper({ steps }: StepperProps) {
  return (
    <div className="w-full relative flex sm:flex-col flex-row">
      <div className="[background:linear-gradient(270.01deg,#2FA68A_14.24%,#3FA1AE_97.29%)] sm:w-full sm:h-2.5 h-80 w-2.5 rounded-md"></div>
      <div className="sm:h-2.5 w-full absolute inset-0 px-4 xl:pl-10 xl:pr-9 flex sm:flex-row flex-col sm:items-center sm:max-w-full max-w-max -left-7 sm:left-0 justify-between h-80">
        <div className="p-1.5 bg-[#F3F5F7] border border-[#E5E8EE] rounded-full">
          <div className="size-6 rounded-full bg-white drop-shadow" />
        </div>
        <div className="p-1.5 bg-[#F3F5F7] border border-[#E5E8EE] rounded-full">
          <div className="size-6 rounded-full bg-white drop-shadow" />
        </div>
        <div className="p-1.5 bg-[#F3F5F7] border border-[#E5E8EE] rounded-full">
          <div className="size-6 rounded-full bg-white drop-shadow" />
        </div>
      </div>
      <div className="sm:mt-7 sm:ml-0 ml-10">
        <div className="flex sm:flex-row flex-col sm:items-center justify-between h-full sm:h-auto">
          {steps.map((step) => (
            <span className="sm:max-w-36 text-center leading-[22px] text-passiveLinkColor">
              {step.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export { Stepper };
