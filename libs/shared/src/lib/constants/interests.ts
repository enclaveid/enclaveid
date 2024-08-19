export interface DisplayableInterest {
  title: string;
  description: string;
  activityType: string;
  similarityPercentage?: number;
  activityDates?: string[];
  pipelineClusterId?: number;
  isViewed?: boolean;
  isSensitive: boolean;
  socialLikelihood: number;
}
