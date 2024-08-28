import { ReactElement } from 'react';
import { trpc } from '../../utils/trpc';
import { PersonalityContentProps } from '../PersonalityContent';
import React from 'react';
import {
  getBigFiveProps,
  getMbtiProps,
} from '../../utils/apiResultsToCardProps';
import {
  BigFivePartial,
  MbtiPartial,
  SixteenPersonalityFactorPartial,
} from '@enclaveid/shared';

export function PersonalityContainer({
  children,
}: {
  children: ReactElement<PersonalityContentProps>;
}) {
  const personalityQuery = trpc.private.getPersonalityTraits.useQuery();

  const bigfive = personalityQuery.data?.bigfive as BigFivePartial;
  const sixteenPersonalityFactor = personalityQuery.data
    ?.sixteenPersonalityFactor as SixteenPersonalityFactorPartial;
  const mbti = personalityQuery.data?.mbti as MbtiPartial;

  return React.cloneElement(children, {
    bigFive: bigfive ? getBigFiveProps(bigfive) : undefined,
    sixteenPersonalityFactor: null,
    mbti: mbti ? getMbtiProps(mbti) : undefined,
    isLoading: personalityQuery.isLoading,
  });
}
