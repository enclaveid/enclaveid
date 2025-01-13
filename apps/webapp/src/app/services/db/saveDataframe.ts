import { prisma } from './prisma';

export interface DataframeRow {
  // UserClaim fields
  label: string;
  description: string;
  node_type: 'observable' | 'inferrable' | 'speculative';
  conversation_id: string;
  frequency: number;
  // ClaimCategory fields
  category: string;
  cluster_label: number;
  is_personal: boolean;
}

export async function saveDataframe(
  userId: string,
  data: DataframeRow[]
): Promise<void> {
  try {
    await prisma.$transaction(async (prisma) => {
      // Bulk insert categories
      const categories = await prisma.claimCategory.createManyAndReturn({
        data: data.map((row) => ({
          name: row.category,
          clusterLabel: row.cluster_label,
          isPersonal: row.is_personal,
        })),
        skipDuplicates: true,
      });

      // Create a map of category attributes to ID for lookup
      const categoryIdMap = new Map(
        categories.map((cat) => [
          `${cat.name}-${cat.clusterLabel}-${cat.isPersonal}`,
          cat.id,
        ])
      );

      // Bulk insert claims
      await prisma.userClaim.createMany({
        data: data.map((row) => ({
          label: row.label,
          description: row.description,
          nodeType: row.node_type,
          conversationId: row.conversation_id,
          frequency: row.frequency,
          claimCategoryId: categoryIdMap.get(
            `${row.category}-${row.cluster_label}-${row.is_personal}`
          )!,
          userId: userId,
        })),
      });
    });
  } catch (error) {
    if (error instanceof Error) {
      console.error('Error saving dataframe:', {
        message: error.message,
        stack: error.stack,
      });
    }
    throw error;
  }
}
