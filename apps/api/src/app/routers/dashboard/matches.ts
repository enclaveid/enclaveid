import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { router, authenticatedProcedure } from '../../trpc';
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { UserMatchOverview } from '@enclaveid/shared';
import { localGeocoderLookup } from '../../services/localGeocoder';

const SIMILARITY_THRESHOLD = 0.9;

export const matches = router({
  getPeopleCount: authenticatedProcedure.query(async () => {
    return await prisma.user.count();
  }),
  getUserMatches: authenticatedProcedure.query(async (opts) => {
    const {
      user: { id: userId },
    } = opts.ctx as AppContext;

    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: {
        userMatches: {
          include: {
            usersOverallSimilarity: {
              include: {
                userMatches: {
                  include: {
                    user: true,
                  },
                },
              },
            },
          },
        },
      },
    });

    return await Promise.all(
      user.userMatches
        .map(async (userMatch) => {
          const { user: otherUser } =
            userMatch.usersOverallSimilarity.userMatches.find(
              (r) => r.user.id != userId,
            );

          if (!otherUser) return null;

          return {
            displayName: otherUser.displayName,
            gender: otherUser.gender,
            humanReadableGeography: await localGeocoderLookup(
              otherUser.geographyLat,
              otherUser.geographyLon,
            ),
            usersOverallSimilarityId: userMatch.usersOverallSimilarity.id,
            overallSimilarity:
              userMatch.usersOverallSimilarity.overallSimilarity,
          };
        })
        .filter((r) => r != null),
    ).then(
      (r) =>
        r.sort(
          (a, b) => b.overallSimilarity - a.overallSimilarity,
        ) as UserMatchOverview[],
    );
  }),
  getUserMatchDetails: authenticatedProcedure
    .input(
      z.object({
        usersOverallSimilarityId: z.string().min(1),
      }),
    )
    .query(async (opts) => {
      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      const { usersOverallSimilarityId } = opts.input;

      const userMatch = await prisma.usersOverallSimilarity
        .findUniqueOrThrow({
          where: {
            id: usersOverallSimilarityId,
          },
          include: {
            userMatches: {
              include: {
                user: {
                  include: {
                    userTraits: {
                      include: {
                        bigFive: true,
                        moralFoundations: true,
                      },
                    },
                    userInterests: {
                      include: {
                        interests: {
                          include: {
                            interestsClusterMatches: true,
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        })
        .catch((e) => {
          throw new TRPCError({
            code: 'UNAUTHORIZED',
            message: e,
          });
        });

      const [currentUser, otherUser] = userMatch.userMatches
        .map((r) => r.user)
        .sort((a, b) => (a.id == userId ? -1 : 1));

      const currentInterestsIds = currentUser.userInterests.interests.map(
        (r) => r.id,
      );
      const otherInterestsIds = otherUser.userInterests.interests.map(
        (r) => r.id,
      );

      const interestsClustersSimilarities =
        await prisma.interestsClustersSimilarity
          .findMany({
            where: {
              cosineSimilarity: {
                gte: SIMILARITY_THRESHOLD,
              },
            },
            include: {
              interestsClusterMatches: {
                where: {
                  OR: [
                    {
                      interestsClusterId: {
                        in: currentInterestsIds,
                      },
                    },
                    {
                      interestsClusterId: {
                        in: otherInterestsIds,
                      },
                    },
                  ],
                },
                include: {
                  interestsCluster: true,
                },
              },
            },
          })
          .then((r) => {
            // Filter out matches that don't have both users
            return r.filter((r) => r.interestsClusterMatches.length == 2);
          });

      const matchingCurrentUserInterests =
        interestsClustersSimilarities.flatMap((ics) => {
          return ics.interestsClusterMatches
            .filter((icm) =>
              currentInterestsIds.includes(icm.interestsClusterId),
            )
            .flatMap((r) => {
              return {
                summary: r.interestsCluster.summary,
                activityType: r.interestsCluster.clusterType,
                cosineSimilarity: ics.cosineSimilarity,
              };
            });
        });

      return {
        userInfo: {
          displayName: otherUser.displayName,
          gender: otherUser.displayName,
          geography: {
            latitude: otherUser.geographyLat,
            longitude: otherUser.geographyLon,
          },
        },
        personality: {
          bigFive: otherUser.userTraits.bigFive,
          moralFoundations: otherUser.userTraits.moralFoundations,
        },
        proactiveInterests: matchingCurrentUserInterests.filter(
          (r) => r.activityType == 'proactive',
        ),
        reactiveInterests: matchingCurrentUserInterests.filter(
          (r) => r.activityType == 'reactive',
        ),
      };
    }),
});
