import type { Gender } from '@prisma/client';

export const TRPC_PUBLIC_NAMESPACE = 'public';
export const TRPC_PRIVATE_NAMESPACE = 'private';
export const TRPC_PREFIX = '/trpc';

export interface UserMatchOverview {
  displayName: string;
  gender: Gender;
  humanReadableGeography: string;
  userMatchId: string;
  overallMatch: number;
}
