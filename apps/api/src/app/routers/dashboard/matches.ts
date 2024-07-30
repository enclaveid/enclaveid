import { prisma } from '@enclaveid/backend';
import { AppContext } from '../../context';
import { router, authenticatedProcedure } from '../../trpc';
import { UserMatch } from '@prisma/client';
import { z } from 'zod';
import { TRPCError } from '@trpc/server';
import { UserMatchOverview } from '@enclaveid/shared';
import { localGeocoderLookup } from '../../services/localGeocoder';

async function parseMatch(
  userMatch: UserMatch,
  direction: 'fromUser' | 'toUser',
) {
  return {
    displayName: userMatch[direction].displayName,
    gender: userMatch[direction].gender,
    humanReadableGeography: await localGeocoderLookup(
      userMatch[direction].geographyLat,
      userMatch[direction].geographyLon,
    ),

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

    return await Promise.all([
      ...user.fromMatches.map((match) => parseMatch(match, 'toUser')),
      ...user.toMatches.map((match) => parseMatch(match, 'fromUser')),
    ]).then(
      (r) =>
        r
          .flat()
          .sort(
            (a, b) => b.overallMatch - a.overallMatch,
          ) as UserMatchOverview[],
    );
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

      const currentInterestsIds = currentUser.userInterests.interests.map(
        (r) => r.id,
      );
      const otherInterestsIds = otherUser.userInterests.interests.map(
        (r) => r.id,
      );

      const userInterestMatches = await prisma.interestsClusterMatch.findMany({
        where: {
          OR: [
            {
              AND: [
                { fromClusterId: { in: otherInterestsIds } },
                { toClusterId: { in: currentInterestsIds } },
              ],
            },
            {
              AND: [
                { fromClusterId: { in: currentInterestsIds } },
                { toClusterId: { in: otherInterestsIds } },
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
          const interestRecord = currentInterestsIds.includes(r.fromClusterId)
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
