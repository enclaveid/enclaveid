import React from 'react';
import { PurposeSelectionProps } from '../onboarding/PurposeSelection';
import { Purpose } from '@prisma/client';
import { trpc } from '../../utils/trpc';

export function PurposeSelectionContainer({
  children,
}: {
  children: React.ReactElement<PurposeSelectionProps>;
}) {
  const { mutate: mutatePurposes } = trpc.private.updatePurposes.useMutation();
  const trpcUtils = trpc.useUtils();

  const handleSubmit = (selectedOptions: Purpose[]) => {
    mutatePurposes(
      { purposes: selectedOptions },
      {
        onSuccess: () => {
          trpcUtils.private.getOnboardingStatus.invalidate();
        },
      },
    );
  };

  return React.cloneElement(children, { handleSubmit });
}
