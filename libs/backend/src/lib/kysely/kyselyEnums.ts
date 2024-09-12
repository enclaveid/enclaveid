export const ActivityType = {
  knowledge_progression: 'knowledge_progression',
  reactive_needs: 'reactive_needs',
  unknown: 'unknown',
} as const;
export type ActivityType = (typeof ActivityType)[keyof typeof ActivityType];
export const Gender = {
  Male: 'Male',
  Female: 'Female',
  Other: 'Other',
} as const;
export type Gender = (typeof Gender)[keyof typeof Gender];
export const Purpose = {
  AnalyzingMyself: 'AnalyzingMyself',
  Dating: 'Dating',
  FindingTravelBuddies: 'FindingTravelBuddies',
  FindingRoomates: 'FindingRoomates',
  FindingProjectCollaborators: 'FindingProjectCollaborators',
  FormingAStudyGroup: 'FormingAStudyGroup',
  MakingFriendsInANewCity: 'MakingFriendsInANewCity',
  FindingGymBuddies: 'FindingGymBuddies',
  FindingALanguageTeacher: 'FindingALanguageTeacher',
} as const;
export type Purpose = (typeof Purpose)[keyof typeof Purpose];
export const DataProvider = {
  GOOGLE: 'GOOGLE',
  FACEBOOK: 'FACEBOOK',
  OPENAI: 'OPENAI',
} as const;
export type DataProvider = (typeof DataProvider)[keyof typeof DataProvider];
