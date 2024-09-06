import {
  TRPC_PRIVATE_NAMESPACE,
  TRPC_PUBLIC_NAMESPACE,
} from '@enclaveid/shared';

import { authentication } from './routers/authentication';
import { attestation } from './routers/attestation';
import { mergeRouters, router } from './trpc';
import { career } from './routers/dashboard/career';
import { politics } from './routers/dashboard/politics';
import { personality } from './routers/dashboard/personality';
import { fakeOauth } from './routers/fakeOauth';
import { fileUpload } from './routers/onboarding/fileUpload';
import { authUtils } from './routers/authUtils';
import { matches } from './routers/dashboard/matches';
import { streamChat } from './routers/dashboard/streamChat';
import { interests } from './routers/dashboard/interests';
import { onboardingStatus } from './routers/onboarding/onboardingStatus';
import { emailConfirmation } from './routers/onboarding/emailConfirmation';
import { updateUser } from './routers/updateUser';
import { settings } from './routers/settings';

export const appRouter = router({
  [TRPC_PRIVATE_NAMESPACE]: mergeRouters(
    personality,
    career,
    politics,
    interests,
    fakeOauth,
    fileUpload,
    authUtils,
    matches,
    streamChat,
    updateUser,
    onboardingStatus,
    emailConfirmation,
    settings,
  ),
  [TRPC_PUBLIC_NAMESPACE]: mergeRouters(attestation, authentication),
});

export type AppRouter = typeof appRouter;
