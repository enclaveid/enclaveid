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
  const isBigFiveComplete = user?.userTraits?.bigFive?.length > 0;

  // Check if moral foundations is complete
  const isMoralFoundationsComplete =
    user?.userTraits?.moralFoundations?.length > 0;

  // Check if data is uploaded
  const isUserDataUploaded = await getIsUserDataUploaded(userId);

  // Check if data has finished processing
  const isDataProcessed = !!user?.userInterests;

  return {
    isBasicProfileComplete,
    isPurposesComplete,
    isBigFiveComplete,
    isMoralFoundationsComplete,
    isUserDataUploaded,
    isDataProcessed,
  };
}
