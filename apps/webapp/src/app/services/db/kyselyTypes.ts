import type { ColumnType } from 'kysely';
export type Generated<T> = T extends ColumnType<infer S, infer I, infer U>
  ? ColumnType<S, I | undefined, U>
  : ColumnType<T, T | undefined, T>;
export type Timestamp = ColumnType<Date, Date | string, Date | string>;

import type { NodeType } from './kyselyEnums';

export type ClaimCategory = {
  id: Generated<number>;
  name: string;
  clusterLabel: number;
  isPersonal: boolean;
};
export type User = {
  id: Generated<number>;
  email: string;
  name: string | null;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
};
export type UserClaim = {
  id: Generated<number>;
  label: string;
  description: string;
  nodeType: NodeType;
  conversationId: string;
  frequency: number;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  claimCategoryId: number;
  userId: number;
};
export type WhitelistedEmail = {
  id: Generated<number>;
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
