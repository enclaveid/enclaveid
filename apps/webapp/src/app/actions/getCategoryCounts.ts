'use server';

import { prisma } from '../services/db/prisma';
import { getCurrentUser } from './getCurrentUser';

export async function getCategoryCounts() {
  const user = await getCurrentUser();

  if (!user) {
    return [];
  }

  const categories = await prisma.claimCategory.findMany({
    where: { userId: user.id },
    include: {
      _count: {
        select: {
          userClaims: true,
        },
      },
    },
  });

  return categories.map((category) => ({
    id: category.id,
    name: category.name,
    count: category._count.userClaims,
  }));
}
