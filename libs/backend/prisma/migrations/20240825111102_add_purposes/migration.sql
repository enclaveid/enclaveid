-- CreateEnum
CREATE TYPE "Purpose" AS ENUM ('AnalyzingMyself', 'Dating', 'FindingTravelBuddies', 'FindingRoomates', 'FindingProjectCollaborators', 'FormingAStudyGroup', 'MakingFriendsInANewCity', 'FindingGymBuddies', 'FindingALanguageTeacher');

-- AlterTable
ALTER TABLE "User" ADD COLUMN     "purposes" "Purpose"[];
