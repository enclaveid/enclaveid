import React from 'react';
import { RequireAuth } from '../../providers/AuthProvider';
import { PurposeSelection } from '../../components/onboarding/PurposeSelection';

export function PurposeSelectionPage() {
  return (
    <RequireAuth>
      <PurposeSelection />
    </RequireAuth>
  );
}
