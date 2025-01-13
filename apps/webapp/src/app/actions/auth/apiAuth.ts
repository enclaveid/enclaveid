import { prisma } from '../../services/db/prisma';

import type { NextRequest } from 'next/server';

export async function apiAuth(req: NextRequest) {
  // Authenticate user using API key
  const authHeader = req.headers.get('authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    throw new Error('Invalid authorization header');
  }
  const apiKey = authHeader.slice(7);

  // Verify API key and get user
  const apiKeyRecord = await prisma.apiKey.findUnique({
    where: { key: apiKey },
    include: { user: true },
  });

  if (!apiKeyRecord) {
    throw new Error('Invalid API key');
  }

  return apiKeyRecord.user;
}
