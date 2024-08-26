import { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  fullWidth?: boolean;
}

function Input({ fullWidth, ...rest }: InputProps) {
  return (
    <div className={`mt-[2px] ${fullWidth ? 'w-full' : 'px-20'}`}>
      <input
        {...rest}
        className={`block pt-2.5 pb-[11px] pl-[13px] pr-6 rounded-md border border-[#E5E8EE] bg-transparent text-black focus:outline-none ${
          fullWidth ? 'w-full' : 'px-20'
        }`}
      />
    </div>
  );
}

export { Input };
