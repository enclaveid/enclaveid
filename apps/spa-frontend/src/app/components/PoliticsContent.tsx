import { CompassSection, CompassSectionProps } from './CompassSection';
import { MFTSection, MFTSectionProps } from './MFTSection';

export interface PoliticsContentProps {
  isLoading?: boolean;
  moralFoundations?: MFTSectionProps;
  politicalCompass?: CompassSectionProps;
}

export function PoliticsContent(props: PoliticsContentProps) {
  const { isLoading } = props;

  return (
    <div className="grid min-[1150px]:grid-cols-2 grid-cols-1 gap-5 mt-3.5">
      <CompassSection {...props.politicalCompass} isLoading={isLoading} />
      <MFTSection {...props.moralFoundations} isLoading={isLoading} />
    </div>
  );
}
