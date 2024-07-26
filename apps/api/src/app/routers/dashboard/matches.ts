import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { router, authenticatedProcedure } from '../../trpc';
import { UserMatch } from '@prisma/client';
import { z } from 'zod';
import { TRPCError } from '@trpc/server';

function parseMatch(userMatch: UserMatch, direction: 'fromUser' | 'toUser') {
  return {
    displayName: userMatch[direction].displayName,
    gender: userMatch[direction].gender,
    geography: {
      latitude: userMatch[direction].geographyLat,
      longitude: userMatch[direction].geographyLon,
    },
    userMatchId: userMatch.id,
    overallMatch: userMatch.overallMatch,
  };
}

const userMatchDetailsSelector = {
  select: {
    displayName: true,
    gender: true,
    geographyLat: true,
    geographyLon: true,
  },
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
            fromMatches: true,
            toMatches: true,
          },
        },
      },
    },
  },
};

export const matches = router({
  getUserMatches: authenticatedProcedure.query(async (opts) => {
    const {
      user: { id: userId },
    } = opts.ctx as AppContext;

    const user = await prisma.user.findUnique({
      where: { id: userId },
      include: {
        fromMatches: {
          include: {
            toUser: true,
          },
        },
        toMatches: {
          include: {
            fromUser: true,
          },
        },
      },
    });

    return [
      user.fromMatches.map((match) => parseMatch(match, 'toUser')),
      user.toMatches.map((match) => parseMatch(match, 'fromUser')),
    ]
      .flat()
      .sort((a, b) => b.overallMatch - a.overallMatch);
  }),
  getUserMatchDetails: authenticatedProcedure
    .input(
      z.object({
        userMatchId: z.string(),
      }),
    )
    .query(async (opts) => {
      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      const { userMatchId } = opts.input;

      const userMatch = await prisma.userMatch
        .findUniqueOrThrow({
          where: {
            id: userMatchId,
            AND: [
              {
                OR: [{ fromUserId: userId }, { toUserId: userId }],
              },
            ],
          },
          include: {
            toUser: userMatchDetailsSelector,
            fromUser: userMatchDetailsSelector,
          },
        })
        .catch((e) => {
          throw new TRPCError({
            code: 'UNAUTHORIZED',
            message: e,
          });
        });

      const [currentUser, otherUser] =
        userMatch.fromUserId == userId
          ? [userMatch.fromUser, userMatch.toUser]
          : [userMatch.toUser, userMatch.fromUser];

      const currentUserInterestsIds = currentUser.userInterests.interests.map(
        (r) => r.id,
      );
      const otherUserInterestsIds = otherUser.userInterests.interests.map(
        (r) => r.id,
      );

      const userInterestMatches = await prisma.interestsClusterMatch.findMany({
        where: {
          OR: [
            {
              AND: [
                { fromClusterId: { in: otherUserInterestsIds } },
                { toClusterId: { in: currentUserInterestsIds } },
              ],
            },
            {
              AND: [
                { fromClusterId: { in: currentUserInterestsIds } },
                { toClusterId: { in: otherUserInterestsIds } },
              ],
            },
          ],
        },
        include: {
          fromCluster: true,
          toCluster: true,
        },
      });

      const allInterests = userInterestMatches
        .map((r) => {
          // We show the current user's summaries for privacy
          const interestRecord = currentUserInterestsIds.includes(
            r.fromClusterId,
          )
            ? r.fromCluster
            : r.toCluster;

          return {
            summary: interestRecord.summary,
            activityType: interestRecord.clusterType,
            cosineSimilarity: r.cosineSimilarity,
          };
        })
        .sort((a, b) => b.cosineSimilarity - a.cosineSimilarity);

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
        proactiveInterests: allInterests.filter(
          (r) => r.activityType == 'proactive',
        ),
        reactiveInterests: allInterests.filter(
          (r) => r.activityType == 'reactive',
        ),
      };
    }),
});
