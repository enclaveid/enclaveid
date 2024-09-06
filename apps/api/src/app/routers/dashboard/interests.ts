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
          sort: z.enum(['prevalence', 'time']).default('prevalence'),
          // activityTypes: z
          //   .array(z.nativeEnum(ActivityType))
          //   .default([
          //     ActivityType.knowledge_progression,
          //     ActivityType.reactive_needs,
          //   ]),
        })
        .default({
          limit: MAX_PAGINATION_LIMIT,
          cursor: '',
          sort: 'prevalence',
          // activityTypes: [
          //   ActivityType.knowledge_progression,
          //   ActivityType.reactive_needs,
          // ],
        }),
    )
    .query(async (opts) => {
      const {
        limit,
        cursor,
        sort,
        // activityTypes
      } = opts.input;

      const {
        user: { id: userId },
      } = opts.ctx as AppContext;

      const inrerestsCount = await prisma.interestsCluster.count({
        where: {
          userInterests: {
            userId,
          },
        },
      });

      // There is no way to paginate with the last item of an array in Prisma
      // https://github.com/prisma/prisma/issues/5560
      const userInterests = (await prisma.$queryRaw`
        WITH ranked_interests AS (
          SELECT
            i.*,
            i."activityDates"[array_length(i."activityDates", 1)] as last_activity_date,
            LPAD(array_length(i."activityDates", 1)::text, 10, '0') as activity_count,
            ROW_NUMBER() OVER (
              ORDER BY
                CASE
                  WHEN ${sort} = 'prevalence' THEN LPAD(array_length(i."activityDates", 1)::text, 10, '0')
                  ELSE i."activityDates"[array_length(i."activityDates", 1)]
                END DESC,
                CASE
                  WHEN ${sort} = 'prevalence' THEN i."activityDates"[array_length(i."activityDates", 1)]
                  ELSE LPAD(array_length(i."activityDates", 1)::text, ${inrerestsCount.toString().length + 1}::int, '0') -- We need to pad the activity count to ensure the sort is correct (can't sort on different data types)
                END DESC
            ) as row_num
          FROM "InterestsCluster" i
          JOIN "UserInterests" ui ON i."userInterestsId" = ui.id
          WHERE ui."userId" = ${userId}
        )
        SELECT *
        FROM ranked_interests
        WHERE row_num > COALESCE((
          SELECT row_num
          FROM ranked_interests
          WHERE id = ${cursor}
        ), 0)
        ORDER BY
          CASE
            WHEN ${sort} = 'prevalence' THEN activity_count
            ELSE last_activity_date
          END DESC,
          CASE
            WHEN ${sort} = 'prevalence' THEN last_activity_date
            ELSE activity_count
          END DESC
        LIMIT ${limit + 1} -- Fetch one more item to determine if there is a next page
        `) as any[];

      let nextCursor: typeof cursor | undefined = undefined;
      if (userInterests.length > limit) {
        const nextItem = userInterests.pop();
        nextCursor = nextItem.id;
      }

      return {
        nextCursor,
        userInterests: userInterests.map((interest) => {
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
        }),
      };
    }),
});
