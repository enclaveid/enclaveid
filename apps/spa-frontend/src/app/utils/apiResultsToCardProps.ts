// TODO: This file serves as a compatibility layer between the API results and the card props since the card props are fucked up

import {
  BigFivePartial,
  MbtiPartial,
  mbtiToString,
  MoralFoundationsPartial,
  PoliticalCompassPartial,
} from '@enclaveid/shared';
import { TraitCardProps } from '../components/BigFiveCard';
import { MbtiCardProps } from '../components/MbtiCard';
import { MFTSectionProps } from '../components/MFTSection';
import { CompassSectionProps } from '../components/CompassSection';
import { getBigFiveTraitDescription } from './traitDescriptions/bigFive';
import { getMbtiTraitDescription } from './traitDescriptions/mbti';
import { getPoliticalCompassTraitDescription } from './traitDescriptions/politicalCompass';
import { getMoralFoundationsTraitDescription } from './traitDescriptions/mft';

export function getBigFiveProps(data: BigFivePartial): TraitCardProps {
  return {
    data: Object.entries(data).map(([key, value]) => ({
      label: key.charAt(0).toUpperCase() + key.slice(1),
      value: value * 100,
      description: getBigFiveTraitDescription(key, value),
    })),
  };
}

export function getMbtiProps(data: MbtiPartial): MbtiCardProps {
  const { shortDescription, longDescription } = getMbtiTraitDescription(data);
  const mbtiString = mbtiToString(data);

  return {
    label: mbtiString,
    description: shortDescription,
    data: {
      title: mbtiString,
      content: longDescription,
    },
  };
}

export function getMFTProps(data: MoralFoundationsPartial): MFTSectionProps {
  return {
    data: {
      harm: data.careHarm,
      fairness: data.fairnessCheating,
      authority: data.authoritySubversion,
      ingroup: data.loyaltyBetrayal,
      purity: data.sanctityDegradation,
      description: getMoralFoundationsTraitDescription(data),
      mftChartAvailable: true,
      error: false,
      loading: false,
    },
  };
}

export function getPoliticalCompassProps(
  data: PoliticalCompassPartial,
): CompassSectionProps {
  return {
    data: {
      x: data.economic * 5,
      y: data.social * 5,
      description: getPoliticalCompassTraitDescription(data),
      compassChartAvailable: true,
      error: false,
      loading: false,
    },
  };
}
