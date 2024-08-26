import { AnchorHTMLAttributes } from 'react';

interface LinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  underlined?: boolean;
}

function Link({ underlined = true, ...props }: LinkProps) {
  const className = `text-greenBg text-center font-medium leading-[22.4px] ${
    underlined ? 'underline' : ''
  }`;

  return (
    <a {...props} className={className}>
      {props.children}
    </a>
  );
}

export { Link };
