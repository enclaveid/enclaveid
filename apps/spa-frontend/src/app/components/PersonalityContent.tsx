import { BigFiveCard, TraitCardProps } from './BigFiveCard';
import { MbtiCard, MbtiCardProps } from './MbtiCard';
import { SixteenPFCard, SixteenPFCardProps } from './SixteenPFCard';

export interface PersonalityContentProps {
  bigFive?: TraitCardProps;
  sixteenPersonalityFactor?: SixteenPFCardProps;
  mbti?: MbtiCardProps;
  isLoading?: boolean;
}

function PersonalityContent(props: PersonalityContentProps) {
  const { isLoading } = props;

  return (
    <div className="pt-3.5 pb-9">
      <div className="grid grid-cols-1 lg:grid-cols-2 md:gap-10 gap-16 lg:gap-5">
        <div className="flex flex-col gap-16 sm:gap-3 lg:gap-3.5">
          <BigFiveCard data={props.bigFive?.data} isLoading={isLoading} />
          <MbtiCard
            label={props.mbti?.label}
            description={props.mbti?.description}
            data={props.mbti?.data}
            isLoading={isLoading}
          />
        </div>
        <SixteenPFCard data={props.sixteenPersonalityFactor?.data} />
      </div>
    </div>
  );
}

export { PersonalityContent };
