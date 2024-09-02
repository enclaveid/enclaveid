import { ActivityType } from '@prisma/client';

export interface DisplayableInterest {
  title: string;
  description: string;
  activityType: ActivityType;
  similarityPercentage?: number;
  activityDates?: string[];
  pipelineClusterId?: number;
  isViewed?: boolean;
  isSensitive: boolean;
  socialLikelihood?: number;
  clusterItems?: string[];
}
