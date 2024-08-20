import { prisma } from '@enclaveid/backend';
import { Prisma } from '@prisma/client';
import { calculateOverallSimilarity } from './userMatchesCalc';

export async function processUserMatches(userId: string) {
  return await prisma.$transaction(async (tx) => {
    // Get all InterestsClustersSimilarity records for the user
    const clusterSimilarities = await tx.interestsClustersSimilarity.findMany({
      where: {
        interestsClusterMatches: {
          some: {
            interestsCluster: {
              userInterests: {
                userId: userId,
              },
            },
          },
        },
      },
      include: {
        interestsClusterMatches: {
          include: {
            interestsCluster: {
              include: {
                userInterests: {
                  include: {
                    user: {
                      include: {
                        userTraits: {
                          include: {
                            bigFive: {
                              take: 1,
                            },
                            moralFoundations: {
                              take: 1,
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    });

    // Group similarities by other user
    const userSimilarities = new Map<
      string,
      {
        proactiveSimilarities: number[];
        reactiveSimilarities: number[];
        otherUserTraits: Prisma.UserTraitsGetPayload<{
          include: {
            bigFive: {
              take: 1;
            };
            moralFoundations: {
              take: 1;
            };
          };
        }>;
      }
    >();

    for (const similarity of clusterSimilarities) {
      const [userCluster, otherUserCluster] =
        similarity.interestsClusterMatches;
      const otherUserId =
        otherUserCluster.interestsCluster.userInterests.userId === userId
          ? userCluster.interestsCluster.userInterests.userId
          : otherUserCluster.interestsCluster.userInterests.userId;

      if (!userSimilarities.has(otherUserId)) {
        userSimilarities.set(otherUserId, {
          proactiveSimilarities: [],
          reactiveSimilarities: [],
          otherUserTraits:
            otherUserCluster.interestsCluster.userInterests.user.userTraits,
        });
      }

      const userSimilarity = userSimilarities.get(otherUserId);
      if (
        similarity.interestsClusterMatches.some(
          (icm) => icm.interestsCluster.clusterType === 'proactive',
        )
      ) {
        userSimilarity.proactiveSimilarities.push(similarity.cosineSimilarity);
      } else {
        userSimilarity.reactiveSimilarities.push(similarity.cosineSimilarity);
      }
    }

    // Get current user's traits
    const currentUserTraits = await tx.userTraits.findUnique({
      where: { userId: userId },
      include: {
        bigFive: {
          take: 1,
        },
        moralFoundations: {
          take: 1,
        },
      },
    });

    if (!currentUserTraits) {
      throw new Error(`UserTraits not found for user ${userId}`);
    }

    // Calculate overall similarity and upsert UsersOverallSimilarity
    for (const [otherUserId, similarity] of userSimilarities) {
      const overallSimilarityScore = calculateOverallSimilarity(
        {
          moralFoundations: currentUserTraits.moralFoundations[0],
          bigFive: currentUserTraits.bigFive[0],
        },
        {
          moralFoundations: similarity.otherUserTraits.moralFoundations[0],
          bigFive: similarity.otherUserTraits.bigFive[0],
        },
        similarity.proactiveSimilarities,
        similarity.reactiveSimilarities,
      );

      // Find existing UsersOverallSimilarity
      const existingSimilarity = await tx.usersOverallSimilarity.findFirst({
        where: {
          userMatches: {
            every: {
              userId: {
                in: [userId, otherUserId],
              },
            },
          },
        },
        include: {
          userMatches: true,
        },
      });

      if (existingSimilarity) {
        // Update existing UsersOverallSimilarity
        await tx.usersOverallSimilarity.update({
          where: { id: existingSimilarity.id },
          data: {
            overallSimilarity: overallSimilarityScore,
          },
        });
      } else {
        // Create new UsersOverallSimilarity with userMatches records
        await tx.usersOverallSimilarity.create({
          data: {
            overallSimilarity: overallSimilarityScore,
            userMatches: {
              create: [{ userId: userId }, { userId: otherUserId }],
            },
          },
        });
      }
    }
  });
}
