import { prisma } from '@enclaveid/backend';
import { DataFrame } from 'nodejs-polars';
import { processUserMatches } from './processUserMatches';
import { Prisma } from '@prisma/client';

interface ClusterData {
  // InterestsCluster
  interestsCluster: Prisma.InterestsClusterCreateInput;
  // InterestsClustersSimilarity
  interestsClustersSimilarity?: Prisma.InterestsClustersSimilarityCreateInput;

  // non-db
  other_user_id?: string;
  other_user_cluster_label?: number;
}

export async function processClusterMatches(dataFrame: DataFrame) {
  const userId = dataFrame.getColumn('userId').get(0) as string;

  await prisma.$transaction(async (tx) => {
    // Update or create UserInterests
    const userInterests = await tx.userInterests.upsert({
      where: { userId: userId },
      update: {},
      create: { userId: userId },
    });

    // Process clusters and matches
    const clusterData: ClusterData[] = dataFrame
      .drop(['userId'])
      .toRecords()
      .map((r) => ({
        interestsCluster: {
          pipelineClusterId: r.pipelineClusterId,
          clusterType: r.clusterType,
          summary: r.summary,
          title: r.title,
          isSensitive: r.isSensitive,
          activityDates: r.activityDates,
          clusterItems: r.clusterItems,
          socialLikelihood: r.socialLikelihood,
        },
        interestsClustersSimilarity: r.cosineSimilarity
          ? {
              cosineSimilarity: r.cosineSimilarity,
              commonSummary: r.commonSummary,
              commonTitle: r.commonTitle,
              averageSocialLikelihood: r.averageSocialLikelihood,
            }
          : undefined,
        other_user_id: r.other_user_id,
        other_user_cluster_label: r.other_user_cluster_label,
      })) as ClusterData[];

    for (const cluster of clusterData) {
      // Update or create InterestsCluster
      const interestsCluster = await tx.interestsCluster.upsert({
        where: {
          userInterestsId_pipelineClusterId_clusterType: {
            userInterestsId: userInterests.id,
            pipelineClusterId: cluster.interestsCluster.pipelineClusterId,
            clusterType: cluster.interestsCluster.clusterType,
          },
        },
        update: {
          ...cluster.interestsCluster,
        },
        create: {
          ...cluster.interestsCluster,
          userInterests: {
            connect: { id: userInterests.id },
          },
        },
      });

      // Process match if it exists
      if (cluster.other_user_id && cluster.other_user_cluster_label) {
        const otherUserInterests = await tx.userInterests.findUnique({
          where: { userId: cluster.other_user_id },
        });

        if (otherUserInterests) {
          const otherInterestsCluster = await tx.interestsCluster.findFirst({
            where: {
              userInterestsId: otherUserInterests.id,
              pipelineClusterId: cluster.other_user_cluster_label,
            },
          });

          if (otherInterestsCluster) {
            // Find existing InterestsClustersSimilarity
            const existingSimilarity =
              await tx.interestsClustersSimilarity.findFirst({
                where: {
                  interestsClusterMatches: {
                    every: {
                      interestsClusterId: {
                        in: [interestsCluster.id, otherInterestsCluster.id],
                      },
                    },
                  },
                },
              });

            if (existingSimilarity) {
              // Update existing InterestsClustersSimilarity
              await tx.interestsClustersSimilarity.update({
                where: { id: existingSimilarity.id },
                data: {
                  ...cluster.interestsClustersSimilarity,
                },
              });
            } else {
              // Create new InterestsClustersSimilarity and InterestsClusterMatch
              await tx.interestsClustersSimilarity.create({
                data: {
                  ...cluster.interestsClustersSimilarity,
                  interestsClusterMatches: {
                    create: [
                      { interestsClusterId: interestsCluster.id },
                      { interestsClusterId: otherInterestsCluster.id },
                    ],
                  },
                },
              });
            }
          }
        }
      }
    }
  });

  // Update all the userMatches for the user
  return await processUserMatches(userId);
}
