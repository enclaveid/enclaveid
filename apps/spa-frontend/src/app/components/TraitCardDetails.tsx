import { useLocation } from 'react-router-dom';
import { TraitCardProps } from './BigFiveCard';
import { TraitCard } from './TraitCard';
import { useEffect } from 'react';
import { useBreadcrumb } from '../providers/BreadcrumbContext';

function TraitCardDetails() {
  const location = useLocation();
  const { data } = location.state as TraitCardProps;
  const { setLink } = useBreadcrumb();

  useEffect(() => {
    setLink('OCEAN');
  }, [setLink]);

  return (
    <div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-5 gap-y-[22px] flex-wrap">
        {data.map((item, index) => {
          return <TraitCard {...item} key={index} />;
        })}
      </div>
    </div>
  );
}

export { TraitCardDetails };
