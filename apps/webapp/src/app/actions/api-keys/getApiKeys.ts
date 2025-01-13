'use server';

import { ApiKey } from '@prisma/client';
import { prisma } from '../../services/db/prisma';
import { getCurrentUser } from '../getCurrentUser';

export async function getApiKeys(): Promise<ApiKey[]> {
  const user = await getCurrentUser();

  if (!user) return [];

  const apiKeys = await prisma.apiKey.findMany({
    where: { userId: user.id },
  });

  return apiKeys;
}
