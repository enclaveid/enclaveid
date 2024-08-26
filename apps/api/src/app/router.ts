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
import { settings } from './routers/dashboard/settings';
import { interests } from './routers/dashboard/interests';
import { onboardingStatus } from './routers/onboarding/onboardingStatus';
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
    settings,
    onboardingStatus,
  ),
  [TRPC_PUBLIC_NAMESPACE]: mergeRouters(attestation, authentication),
});

export type AppRouter = typeof appRouter;
