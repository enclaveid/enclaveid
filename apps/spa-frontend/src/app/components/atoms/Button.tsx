import React from 'react';
import classNames from 'classnames';

type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'error';
type ButtonSize = 'small' | 'large';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  fullWidth?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-greenBg shadow text-white pt-[13px] pb-[12px] rounded-md px-8',
  secondary: 'text-greenBg underline bg-transparent',
  tertiary: 'text-passiveLinkColor py-[7px] px-8 bg-white shadow rounded-lg',
  error:
    'py-[11.5px] w-full text-center text-white leading-[18px] font-medium rounded-lg bg-[#A62F2F]',
};

export function Button({
  variant = 'primary',
  label,
  fullWidth,
  size,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      className={classNames(
        'font-medium leading-[22.4px] text-center flex items-center justify-center',
        variantClasses[variant],
        {
          'w-full': fullWidth,
          'text-xs font-normal !leading-4':
            variant === 'secondary' && size === 'small',
          'w-44 h-8': size === 'large',
        },
        className,
      )}
    >
      {label}
    </button>
  );
}
