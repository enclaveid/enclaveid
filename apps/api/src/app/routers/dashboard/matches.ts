import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { router, authenticatedProcedure } from '../../trpc';
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { DisplayableInterest } from '@enclaveid/shared';
import { MAX_PAGINATION_LIMIT } from '../../constants';
import { replaceUserIds } from '../../services/contentPrivacy';
import { ActivityType } from '@prisma/client';

export const matches = router({
  getPeopleCount: authenticatedProcedure.query(async () => {
    return await prisma.user.count();
  }),
  getUserMatches: authenticatedProcedure.query(async (opts) => {
    const {
      user: { id: userId },
    } = opts.ctx as AppContext;

    const user = await prisma.user.findUniqueOrThrow({
      where: { id: userId },
      select: {
        matchingEnabled: true,
      },
    });

    if (!user.matchingEnabled) {
      return [];
    }

    const userMatches = await prisma.userMatch.findMany({
      where: { userId },
      select: {
        usersOverallSimilarity: {
          select: {
            id: true,
            overallSimilarity: true,
            userMatches: {
              where: {
                user: {
                  id: { not: userId },
                  matchingEnabled: true,
                },
              },
              select: {
                user: {
                  select: {
                    displayName: true,
                    gender: true,
                    country: true,
                  },
                },
              },
            },
          },
        },
      },
      orderBy: {
        usersOverallSimilarity: {
          overallSimilarity: 'desc',
        },
      },
    });

    return userMatches.map((match) => ({
      displayName: match.usersOverallSimilarity.userMatches[0].user.displayName,
      gender: match.usersOverallSimilarity.userMatches[0].user.gender,
      country: match.usersOverallSimilarity.userMatches[0].user.country,
      usersOverallSimilarityId: match.usersOverallSimilarity.id,
      overallSimilarity: match.usersOverallSimilarity.overallSimilarity,
    }));
  }),
  getUserMatchDetails: authenticatedProcedure
    .input(
      z.object({
        usersOverallSimilarityId: z.string().min(1),
        limit: z
          .number()
          .min(1)
          .max(MAX_PAGINATION_LIMIT)
          .default(MAX_PAGINATION_LIMIT),
        cursor: z.string().default(''),
        activityTypes: z
          .array(z.nativeEnum(ActivityType))
          .default([
            ActivityType.knowledge_progression,
            ActivityType.reactive_needs,
          ]),
      }),
    )
    .query(async (opts) => {
      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      const { usersOverallSimilarityId, limit, cursor } = opts.input;

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
                          where: {
                            clusterType: {
                              in: opts.input.activityTypes,
                            },
                          },
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

      const showSensitiveInterests =
        currentUser.sensitiveMatchingEnabled &&
        otherUser.sensitiveMatchingEnabled;

      const interestsClustersSimilarities =
        await prisma.interestsClustersSimilarity.findMany({
          take: limit + 1, // get an extra item at the end which we'll use as next cursor
          where: {
            // Matches without summaries or titles are below the similarity and relevance thresholds
            commonSummary: {
              not: null,
            },
            commonTitle: {
              not: null,
            },
            // get only the interestsClustersSimilarities that have matches for both users
            AND: [
              {
                interestsClusterMatches: {
                  some: {
                    interestsClusterId: { in: currentInterestsIds },
                    interestsCluster: showSensitiveInterests
                      ? {} // Include all interests regardless of sensitivity
                      : { isSensitive: false }, // Only include non-sensitive interests
                  },
                },
              },
              {
                interestsClusterMatches: {
                  some: {
                    interestsClusterId: { in: otherInterestsIds },
                    interestsCluster: showSensitiveInterests
                      ? {} // Include all interests regardless of sensitivity
                      : { isSensitive: false }, // Only include non-sensitive interests
                  },
                },
              },
            ],
          },
          cursor: cursor ? { id: cursor } : undefined,
          orderBy: [
            { averageSocialLikelihood: 'desc' },
            { cosineSimilarity: 'desc' },
          ],
          include: {
            interestsClusterMatches: {
              include: {
                interestsCluster: true,
              },
            },
          },
        });

      const matchingCurrentUserInterests =
        interestsClustersSimilarities.flatMap((ics) => {
          return ics.interestsClusterMatches
            .filter((icm) =>
              currentInterestsIds.includes(icm.interestsClusterId),
            )
            .flatMap((r): DisplayableInterest => {
              return {
                title: ics.commonTitle,
                description: replaceUserIds(
                  ics.commonSummary,
                  [userId, otherUser.id],
                  [currentUser.displayName, otherUser.displayName],
                ),
                activityType: r.interestsCluster.clusterType,
                similarityPercentage: ics.cosineSimilarity,
                pipelineClusterId: r.interestsCluster.pipelineClusterId,
                isSensitive: r.interestsCluster.isSensitive,
                socialLikelihood: ics.averageSocialLikelihood,
              };
            });
        });

      let nextCursor: typeof cursor | undefined = undefined;
      if (interestsClustersSimilarities.length > limit) {
        const nextItem = interestsClustersSimilarities.pop();
        nextCursor = nextItem.id;
      }

      return {
        userInfo: {
          displayName: otherUser.displayName,
          gender: otherUser.displayName,
          country: otherUser.country,
        },
        personality: {
          bigFive: otherUser.userTraits.bigFive,
          moralFoundations: otherUser.userTraits.moralFoundations,
        },
        interests: {
          userInterests: matchingCurrentUserInterests,
          nextCursor,
        },
      };
    }),
});
