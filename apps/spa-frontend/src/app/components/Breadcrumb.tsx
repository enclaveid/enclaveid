import classNames from 'classnames';

import { useNavigate, useLocation } from 'react-router-dom';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { useEffect } from 'react';

function Breadcrumb() {
  const navigate = useNavigate();
  const location = useLocation();

  const { link, setLink } = useBreadcrumb();

  const handleDashboardClick = () => {
    if (link) {
      navigate(-1);
      setLink('');
    }
  };

  useEffect(() => {
    const pathSegments = location.pathname
      .split('/')
      .filter((path) => path.length > 0);

    if (pathSegments.length === 2 && pathSegments[0] === 'dashboard') {
      setLink('');
    } else if (pathSegments.length > 2) {
    }
  }, [location, setLink]);

  return (
    <div className="flex gap-1.5 items-center text-[23px] leading-[27px] font-medium">
      <button
        onClick={handleDashboardClick}
        className={classNames(
          link
            ? 'text-active-breadcrumb-title underline'
            : 'text-passiveLinkColor',
        )}
      >
        {location.pathname.startsWith('/dashboard')
          ? 'Traits Dashboard'
          : location.pathname.startsWith('/socials')
            ? 'Explore Social'
            : ''}
      </button>{' '}
      {link && (
        <>
          <span className="text-passiveLinkColor">{'>'}</span>{' '}
          <span className="text-passiveLinkColor">{link}</span>{' '}
        </>
      )}
    </div>
  );
}

export { Breadcrumb };
