import type { ColumnType } from 'kysely';
export type Generated<T> =
  T extends ColumnType<infer S, infer I, infer U>
    ? ColumnType<S, I | undefined, U>
    : ColumnType<T, T | undefined, T>;
export type Timestamp = ColumnType<Date, Date | string, Date | string>;

import type { ActivityType, Gender, Purpose } from './kyselyEnums';

export type BigFive = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  summary: string | null;
  userTraitsId: string;
};
export type ChromePod = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  chromePodId: string;
  hostname: string;
  rdpUsername: string;
  rdpPassword: string;
  rdpPort: number;
};
export type InterestsCluster = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  pipelineClusterId: number;
  clusterType: ActivityType;
  summary: string;
  title: string;
  activityDates: string[];
  isSensitive: Generated<boolean>;
  clusterItems: string[];
  socialLikelihood: number;
  userInterestsId: string;
};
export type InterestsClusterMatch = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  interestsClusterId: string;
  interestsClustersSimilarityId: string;
};
export type InterestsClustersSimilarity = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  averageSocialLikelihood: number;
  cosineSimilarity: number;
  commonSummary: string | null;
  commonTitle: string | null;
};
export type Mbti = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  extraversion: boolean;
  sensing: boolean;
  thinking: boolean;
  judging: boolean;
  summary: string | null;
  userTraitsId: string;
};
export type MoralFoundations = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  careHarm: number;
  fairnessCheating: number;
  loyaltyBetrayal: number;
  authoritySubversion: number;
  sanctityDegradation: number;
  summary: string | null;
  goodCheck: number;
  mathCheck: number;
  userTraitsId: string;
};
export type PoliticalCompass = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  economic: number;
  social: number;
  summary: string | null;
  userTraitsId: string;
};
export type Riasec = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  realistic: number;
  investigative: number;
  artistic: number;
  social: number;
  enterprising: number;
  conventional: number;
  summary: string | null;
  userTraitsId: string;
};
export type Session = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  sessionSecret: Buffer;
  userId: string | null;
};
export type SixteenPersonalityFactor = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  warmth: number;
  reasoning: number;
  emotionalStability: number;
  dominance: number;
  liveliness: number;
  ruleConsciousness: number;
  socialBoldness: number;
  sensitivity: number;
  vigilance: number;
  abstractedness: number;
  privateness: number;
  apprehension: number;
  opennessToChange: number;
  selfReliance: number;
  perfectionism: number;
  tension: number;
  summary: string | null;
  userTraitsId: string;
};
export type User = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  email: string;
  password: string;
  confirmationCode: string;
  confirmedAt: Timestamp | null;
  streamChatToken: string | null;
  displayName: string;
  gender: Gender;
  country: string;
  purposes: Purpose[];
  matchingEnabled: Generated<boolean>;
  sensitiveMatchingEnabled: Generated<boolean>;
  chromePodId: string | null;
};
export type UserInterests = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  userId: string;
};
export type UserMatch = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  userId: string;
  usersOverallSimilarityId: string;
};
export type UsersOverallSimilarity = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  overallSimilarity: number;
};
export type UserTraits = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  userId: string;
};
export type WhitelistedEmail = {
  id: string;
  createdAt: Generated<Timestamp>;
  updatedAt: Timestamp;
  email: string;
};
export type DB = {
  BigFive: BigFive;
  ChromePod: ChromePod;
  InterestsCluster: InterestsCluster;
  InterestsClusterMatch: InterestsClusterMatch;
  InterestsClustersSimilarity: InterestsClustersSimilarity;
  Mbti: Mbti;
  MoralFoundations: MoralFoundations;
  PoliticalCompass: PoliticalCompass;
  Riasec: Riasec;
  Session: Session;
  SixteenPersonalityFactor: SixteenPersonalityFactor;
  User: User;
  UserInterests: UserInterests;
  UserMatch: UserMatch;
  UsersOverallSimilarity: UsersOverallSimilarity;
  UserTraits: UserTraits;
  WhitelistedEmail: WhitelistedEmail;
};
