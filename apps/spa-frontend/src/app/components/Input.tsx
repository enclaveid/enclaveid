import classNames from 'classnames';
import { InputHTMLAttributes, ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  fullWidth?: boolean;
  icon?: ReactNode;
}

function Input({ label, fullWidth, icon, ...rest }: InputProps) {
  return (
    <div>
      <label
        htmlFor={rest.id}
        className="text-[#6C7A8A] text-sm font-medium leading-[19.6px] block"
      >
        {label}
      </label>
      <div className="mt-[2px] relative">
        <input
          {...rest}
          className={classNames(
            'block pt-2.5 pb-[11px] pr-6 rounded-md border border-[#E5E8EE] bg-[#F3F5F7] text-black focus:outline-none',
            fullWidth ? 'w-full' : 'px-20',
            icon ? 'pl-[42px]' : 'pl-[13px]',
          )}
        />
        {icon && (
          <span className="-translate-y-1/2 top-1/2 absolute pl-3.5">
            {icon}
          </span>
        )}
      </div>
    </div>
  );
}

export { Input };
