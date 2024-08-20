import { prisma } from '@enclaveid/backend';
import { DataFrame } from 'nodejs-polars';


interface ClusterData {
  // InterestsCluster
  pipelineClusterId: number;
  clusterType: string;
  summary: string;
  title: string;
  isSensitive: boolean;
  activityDates: string[];
  clusterItems: string[];
  socialLikelihood: number;
  // InterestsClustersSimilarity
  cosineSimilarity?: number;
  commonSummary?: string;
  commonTitle?: string;
  averageSocialLikelihood?: number;
  // non-db
  other_user_id?: string;
  other_user_cluster_label?: number;
}

export async function processClusterMatches(dataFrame: DataFrame): Promise<void> {
  const userId = dataFrame.getColumn('userId').get(0) as string;

  await prisma.$transaction(async (tx) => {
    // Update or create UserInterests
    const userInterests = await tx.userInterests.upsert({
      where: { userId: userId },
      update: {},
      create: { userId: userId },
    });

    // Process clusters and matches
    const clusterData: ClusterData[] = dataFrame.drop(['userId']).toRecords() as ClusterData[];

    for (const cluster of clusterData) {
      // Update or create InterestsCluster
      const interestsCluster = await tx.interestsCluster.upsert({
        where: {
          userInterestsId_pipelineClusterId_clusterType: {
            userInterestsId: userInterests.id,
            pipelineClusterId: cluster.pipelineClusterId,
            clusterType: cluster.clusterType,
          }
        },
        update: {
          summary: cluster.summary,
          title: cluster.title,
          isSensitive: cluster.isSensitive,
          activityDates: cluster.activityDates,
          clusterItems: cluster.clusterItems,
          socialLikelihood: cluster.socialLikelihood,
        },
        create: {
          userInterestsId: userInterests.id,
          pipelineClusterId: cluster.pipelineClusterId,
          clusterType: cluster.clusterType,
          summary: cluster.summary,
          title: cluster.title,
          isSensitive: cluster.isSensitive,
          activityDates: cluster.activityDates,
          clusterItems: cluster.clusterItems,
          socialLikelihood: cluster.socialLikelihood,
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
            const existingSimilarity = await tx.interestsClustersSimilarity.findFirst({
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
                  cosineSimilarity: cluster.cosineSimilarity!,
                  averageSocialLikelihood: cluster.averageSocialLikelihood!,
                  commonSummary: cluster.commonSummary!,
                  commonTitle: cluster.commonTitle!,
                },
              });
            } else {
              // Create new InterestsClustersSimilarity and InterestsClusterMatch
              await tx.interestsClustersSimilarity.create({
                data: {
                  cosineSimilarity: cluster.cosineSimilarity!,
                  averageSocialLikelihood: cluster.averageSocialLikelihood!,
                  commonSummary: cluster.commonSummary!,
                  commonTitle: cluster.commonTitle!,
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
}});
}
