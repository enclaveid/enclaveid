'use server';

import { auth } from '../services/auth';
import { prisma } from '../services/db/prisma';

export async function getApiKey() {
  const session = await auth();

  if (!session?.user) return null;

  const user = await prisma.user.findUnique({
    where: { email: session.user.email! },
    select: { apiKey: true },
  });

  return user?.apiKey;
}
