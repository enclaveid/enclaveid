import { prisma } from '@enclaveid/backend';
import { getIsUserDataUploaded } from './dataPipeline/getIsUserDataUploaded';

export async function getUserOnboardingStatus(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      userTraits: {
        include: {
          bigFive: true,
          moralFoundations: true,
        },
      },
      userInterests: true,
    },
  });

  // Check if basic profile is complete
  const isBasicProfileComplete =
    !!user?.displayName &&
    !!user?.gender &&
    !!user?.geographyLat &&
    !!user?.geographyLon;

  const isPurposesComplete = user?.purposes.length > 0;

  // Check if big five is complete
  const isBigFiveComplete = !!user?.userTraits?.bigFive;

  // Check if moral foundations is complete
  const isMoralFoundationsComplete = !!user?.userTraits?.moralFoundations;

  // Check if data is uploaded
  const isUserDataUploaded = getIsUserDataUploaded(userId);

  return {
    isBasicProfileComplete,
    isPurposesComplete,
    isBigFiveComplete,
    isMoralFoundationsComplete,
    isUserDataUploaded,
  };
}
