import { AppContext } from '../../context';
import { authenticatedProcedure, router } from '../../trpc';
import { getUserOnboardingStatus } from '../../services/getUserOnboardingStatus';
import { prisma } from '@enclaveid/backend';

export const onboardingStatus = router({
  getOnboardingStatus: authenticatedProcedure.query(async ({ ctx }) => {
    const {
      user: { id: userId },
    } = ctx as AppContext;

    return await getUserOnboardingStatus(userId);
  }),
  getEmailConfirmationStatus: authenticatedProcedure.query(async ({ ctx }) => {
    const {
      user: { id: userId },
    } = ctx as AppContext;

    const user = await prisma.user.findUnique({
      where: { id: userId },
    });

    return user?.confirmedAt !== null;
  }),
});
