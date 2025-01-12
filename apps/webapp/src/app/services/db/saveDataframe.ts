import { db } from './db';
import { createId } from '@paralleldrive/cuid2';

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
    await db.transaction().execute(async (trx) => {
      // Group rows by category to avoid duplicate categories
      const categoriesMap = new Map<string, DataframeRow>();
      data.forEach((row) => {
        const key = `${row.category}-${row.cluster_label}-${row.is_personal}`;
        if (!categoriesMap.has(key)) {
          categoriesMap.set(key, row);
        }
      });

      // Bulk insert categories
      const categories = await trx
        .insertInto('ClaimCategory')
        .values(
          Array.from(categoriesMap.values()).map((row) => ({
            id: createId(),
            name: row.category,
            clusterLabel: row.cluster_label,
            isPersonal: row.is_personal,
            updatedAt: new Date(),
          }))
        )
        .returning(['id', 'name', 'clusterLabel', 'isPersonal'])
        .execute();

      // Create a map of category attributes to ID for lookup
      const categoryIdMap = new Map(
        categories.map((cat) => [
          `${cat.name}-${cat.clusterLabel}-${cat.isPersonal}`,
          cat.id,
        ])
      );

      // Bulk insert claims
      await trx
        .insertInto('UserClaim')
        .values(
          data.map((row) => ({
            id: createId(),
            label: row.label,
            description: row.description,
            nodeType: row.node_type,
            conversationId: row.conversation_id,
            frequency: row.frequency,
            claimCategoryId: categoryIdMap.get(
              `${row.category}-${row.cluster_label}-${row.is_personal}`
            )!,
            userId: userId,
            updatedAt: new Date(),
          }))
        )
        .execute();
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
