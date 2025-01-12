import type { ColumnType } from 'kysely';
export type Generated<T> = T extends ColumnType<infer S, infer I, infer U>
  ? ColumnType<S, I | undefined, U>
  : ColumnType<T, T | undefined, T>;
export type Timestamp = ColumnType<Date, Date | string, Date | string>;

import type { NodeType } from './kyselyEnums';

export type ClaimCategory = {
  id: string;
  name: string;
  clusterLabel: number;
  isPersonal: boolean;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
};
export type User = {
  id: string;
  email: string;
  name: string | null;
  apiKey: Generated<string>;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
};
export type UserClaim = {
  id: string;
  label: string;
  description: string;
  nodeType: NodeType;
  conversationId: string;
  frequency: number;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  claimCategoryId: string;
  userId: string;
};
export type WhitelistedEmail = {
  id: string;
  email: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
};
export type DB = {
  ClaimCategory: ClaimCategory;
  User: User;
  UserClaim: UserClaim;
  WhitelistedEmail: WhitelistedEmail;
};
