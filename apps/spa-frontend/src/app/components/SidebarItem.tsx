import { ReactElement, cloneElement } from 'react';
import classNames from 'classnames';
import { Link, useLocation } from 'react-router-dom';

interface SidebarItemProps {
  icon: ReactElement;
  text: string;
  href?: string;
  onClick?: () => void;
}

function SidebarItem({
  icon,
  text,
  href,
  onClick,
}: SidebarItemProps): ReactElement {
  const location = useLocation();

  const activeLinkClass = 'font-semibold text-greenBg';
  const passiveLinkClass = 'font-medium text-passiveLinkColor';

  const active = location.pathname.startsWith(href);

  const iconWithClassName = cloneElement(icon, {
    className: classNames(
      'w-6 h-6',
      active ? 'text-activeIconColor' : 'text-passiveIconColor',
    ),
  });

  const Component = href ? Link : 'button';

  return (
    <Component
      className="flex items-center gap-2.5 px-2.5 py-3 w-full"
      to={href}
      onClick={onClick}
    >
      {iconWithClassName}
      <span
        className={classNames(
          'leading-5',
          active ? activeLinkClass : passiveLinkClass,
        )}
      >
        {text}
      </span>
    </Component>
  );
}

function Chip({ label }: { label: string }) {
  return (
    <div
      className={classNames(
        'py-[2px] px-1.5 rounded-full font-semibold text-white tracking-[0.05em] text-[10px] flex-1 text-right max-w-max ml-auto uppercase',
        label.toLowerCase() === 'preview' ? 'bg-[#4D6C8F]' : 'bg-[#676767]',
      )}
    >
      {label}
    </div>
  );
}

export { SidebarItem };
