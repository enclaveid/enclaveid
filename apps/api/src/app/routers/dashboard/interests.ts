import { prisma } from '@enclaveid/backend';
import { router, authenticatedProcedure } from '../../trpc';
import { z } from 'zod';
import { AppContext } from '../../context';
import { MAX_PAGINATION_LIMIT } from '../../constants';
import { DisplayableInterest } from '@enclaveid/shared';

export const interests = router({
  getUserInterests: authenticatedProcedure
    .input(
      z
        .object({
          limit: z
            .number()
            .min(1)
            .max(MAX_PAGINATION_LIMIT)
            .default(MAX_PAGINATION_LIMIT),
          cursor: z.string().default(''),
          activityTypes: z
            .array(z.string())
            .default(['reactive_needs', 'knowledge_progression']),
        })
        .default({
          limit: MAX_PAGINATION_LIMIT,
          cursor: '',
          activityTypes: ['reactive_needs', 'knowledge_progression'],
        }),
    )
    .query(async (opts) => {
      const { limit, cursor, activityTypes } = opts.input;

      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      // There is no way to paginate with the last item of an array in Prisma
      // https://github.com/prisma/prisma/issues/5560
      const userInterests = (await prisma.$queryRaw`
        WITH ranked_interests AS (
          SELECT
            i.*,
            i."activityDates"[array_length(i."activityDates", 1)] as last_activity_date,
            ROW_NUMBER() OVER (
              ORDER BY i."activityDates"[array_length(i."activityDates", 1)] DESC
            ) as row_num
          FROM "InterestsCluster" i
          JOIN "UserInterests" ui ON i."userInterestsId" = ui.id
          WHERE ui."userId" = ${userId} AND i."clusterType" = ANY(${activityTypes})
        )
        SELECT *
        FROM ranked_interests
        WHERE row_num > COALESCE((
          SELECT row_num
          FROM ranked_interests
          WHERE id = ${cursor}
        ), 0)
        ORDER BY last_activity_date DESC
        LIMIT ${limit + 1} -- Fetch one more item to determine if there is a next page
      `) as any[];

      const results = userInterests.map((interest) => {
        return {
          id: interest.id,
          title: interest.title,
          activityDates: interest.activityDates,
          description: interest.summary,
          clusterType: interest.clusterType,
          pipelineClusterId: interest.pipelineClusterId,
          activityType: interest.clusterType,
          isSensitive: interest.isSensitive,
          clusterItems: interest.clusterItems,
        } as DisplayableInterest & { id: string };
      });

      let nextCursor: typeof cursor | undefined = undefined;
      if (results.length > limit) {
        const nextItem = results.pop();
        nextCursor = nextItem.id;
      }

      return {
        userInterests: results,
        nextCursor,
      };
    }),
});
