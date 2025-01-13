'use server';

import { ApiKey } from '@prisma/client';
import { prisma } from '../../services/db/prisma';
import { getCurrentUser } from '../getCurrentUser';

export async function deleteApiKey(apiKeyId: string): Promise<ApiKey> {
  const user = await getCurrentUser();

  if (!user) throw new Error('Authentication required');

  const apiKey = await prisma.apiKey.delete({
    where: { id: apiKeyId },
  });

  return apiKey;
}
