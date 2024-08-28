import { ReactElement } from 'react';
import { trpc } from '../../utils/trpc';
import React from 'react';
import {
  MoralFoundationsPartial,
  PoliticalCompassPartial,
} from '@enclaveid/shared';
import { PoliticsContentProps } from '../PoliticsContent';
import {
  getMFTProps,
  getPoliticalCompassProps,
} from '../../utils/apiResultsToCardProps';

export function PoliticsContainer({
  children,
}: {
  children: ReactElement<PoliticsContentProps>;
}) {
  const politicsQuery = trpc.private.getPoliticsTraits.useQuery();

  const moralFoundations = politicsQuery.data
    ?.moralFoundations as MoralFoundationsPartial;
  const politicalCompass = politicsQuery.data
    ?.politicalCompass as PoliticalCompassPartial;

  return React.cloneElement(children, {
    isLoading: politicsQuery.isLoading,
    moralFoundations: moralFoundations
      ? getMFTProps(moralFoundations)
      : undefined,
    politicalCompass: politicalCompass
      ? getPoliticalCompassProps(politicalCompass)
      : undefined,
  });
}
