import { AppContext } from '../../context';
import { authenticatedProcedure, router } from '../../trpc';
import { getUserOnboardingStatus } from '../../services/getUserOnboardingStatus';

export const onboardingStatus = router({
  getOnboardingStatus: authenticatedProcedure.query(async ({ ctx }) => {
    const {
      user: { id: userId },
    } = ctx as AppContext;

    return await getUserOnboardingStatus(userId);
  }),
});
