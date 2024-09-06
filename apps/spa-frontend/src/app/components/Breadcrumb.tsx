import { useNavigate, useLocation } from 'react-router-dom';
import { useBreadcrumb } from '../providers/BreadcrumbContext';
import { useEffect } from 'react';
import { sidebarItems } from '../utils/ui/sidebarItems';
import classNames from 'classnames';

const pathToLabelMap = Object.entries(sidebarItems).reduce(
  (acc, [, items]) => {
    items.forEach((item) => {
      acc[item.href] = item.text;
    });
    return acc;
  },
  {} as Record<string, string>,
);

function Breadcrumb() {
  const navigate = useNavigate();
  const location = useLocation();
  const { link, setLink } = useBreadcrumb();

  useEffect(() => {
    // Reset link when location changes
    setLink('');
  }, [location, setLink]);

  const handleDashboardClick = () => {
    if (link) {
      navigate(-1);
      setLink('');
    }
  };

  const getBreadcrumbLabel = () => {
    for (const [path, label] of Object.entries(pathToLabelMap)) {
      if (location.pathname.startsWith(path)) {
        return label;
      }
    }
    return '';
  };

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
        {getBreadcrumbLabel()}
      </button>
      {link && (
        <>
          <span className="text-passiveLinkColor">{'>'}</span>
          <span className="text-passiveLinkColor">{link}</span>
        </>
      )}
    </div>
  );
}

export { Breadcrumb };
