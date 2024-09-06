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
          activityDates: r.activityDates.map(
            (date) => date.toISOString().split('T')[0],
          ),
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

    // Batch upsert InterestsCluster
    await tx.interestsCluster.createMany({
      data: clusterData.map((cluster) => ({
        ...cluster.interestsCluster,
        userInterestsId: userInterests.id,
      })),
      skipDuplicates: true,
    });

    // Fetch created clusters
    const createdClusters = await tx.interestsCluster.findMany({
      where: { userInterestsId: userInterests.id },
      select: { id: true, pipelineClusterId: true },
    });

    // Batch process matches
    const matchData = clusterData.filter(
      (cluster) => cluster.other_user_id && cluster.other_user_cluster_label,
    );

    if (matchData.length > 0) {
      const otherUserIds = matchData.map((cluster) => cluster.other_user_id);
      const otherUserInterests = await tx.userInterests.findMany({
        where: { userId: { in: otherUserIds } },
      });

      const otherUserInterestsMap = new Map(
        otherUserInterests.map((ui) => [ui.userId, ui]),
      );

      const otherClusterLabels = matchData.map(
        (cluster) => cluster.other_user_cluster_label,
      );
      const otherInterestsClusters = await tx.interestsCluster.findMany({
        where: {
          userInterestsId: { in: otherUserInterests.map((ui) => ui.id) },
          pipelineClusterId: { in: otherClusterLabels },
        },
      });

      const otherInterestsClustersMap = new Map(
        otherInterestsClusters.map((ic) => [
          `${ic.userInterestsId}-${ic.pipelineClusterId}`,
          ic,
        ]),
      );

      // Batch create InterestsClustersSimilarity and InterestsClusterMatch
      const similarityData = matchData
        .map((cluster) => {
          const otherUserInterest = otherUserInterestsMap.get(
            cluster.other_user_id,
          );
          const otherInterestsCluster =
            otherUserInterest &&
            otherInterestsClustersMap.get(
              `${otherUserInterest.id}-${cluster.other_user_cluster_label}`,
            );

          if (otherInterestsCluster) {
            return {
              ...cluster.interestsClustersSimilarity,
              currentClusterId: createdClusters.find(
                (ic) =>
                  ic.pipelineClusterId ===
                  cluster.interestsCluster.pipelineClusterId,
              ).id,
              otherClusterId: otherInterestsCluster.id,
            };
          }
        })
        .filter(Boolean);

      // Delete existing InterestsClustersSimilarity records
      await tx.interestsClustersSimilarity.deleteMany({
        where: {
          interestsClusterMatches: {
            some: {
              interestsClusterId: {
                in: similarityData.map((s) => s.currentClusterId),
              },
            },
          },
        },
      });

      // Create InterestsClustersSimilarity records
      await tx.interestsClustersSimilarity.createMany({
        data: similarityData.map(
          ({ currentClusterId, otherClusterId, ...rest }) => rest,
        ),
        skipDuplicates: true,
      });

      // Fetch created similarities
      const fetchedSimilarities = await tx.interestsClustersSimilarity.findMany(
        {
          where: {
            cosineSimilarity: {
              in: similarityData.map((s) => s.cosineSimilarity),
            },
          },
        },
      );

      // Create InterestsClusterMatch records
      const matchRecords = similarityData.flatMap((similarity) => {
        const fetchedSimilarity = fetchedSimilarities.find(
          (fs) => fs.cosineSimilarity === similarity.cosineSimilarity,
        );
        if (fetchedSimilarity) {
          return [
            {
              interestsClustersSimilarityId: fetchedSimilarity.id,
              interestsClusterId: similarity.currentClusterId,
            },
            {
              interestsClustersSimilarityId: fetchedSimilarity.id,
              interestsClusterId: similarity.otherClusterId,
            },
          ];
        }
        return [];
      });

      if (matchRecords.length > 0) {
        await tx.interestsClusterMatch.createMany({
          data: matchRecords,
          skipDuplicates: true,
        });
      }
    }
  });

  // Update all the userMatches for the user
  return await processUserMatches(userId);
}
