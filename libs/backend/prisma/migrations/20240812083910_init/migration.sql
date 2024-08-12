-- CreateEnum
CREATE TYPE "Gender" AS ENUM ('Male', 'Female', 'Other');

-- CreateEnum
CREATE TYPE "DataProvider" AS ENUM ('GOOGLE', 'FACEBOOK', 'OPENAI');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "email" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "confirmationCode" TEXT NOT NULL,
    "confirmedAt" TIMESTAMP(3),
    "streamChatToken" TEXT,
    "displayName" TEXT NOT NULL,
    "gender" "Gender" NOT NULL,
    "geographyLat" DOUBLE PRECISION NOT NULL,
    "geographyLon" DOUBLE PRECISION NOT NULL,
    "chromePodId" TEXT,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Session" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "sessionSecret" BYTEA NOT NULL,
    "userId" TEXT,

    CONSTRAINT "Session_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ChromePod" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "chromePodId" TEXT NOT NULL,
    "hostname" TEXT NOT NULL,
    "rdpUsername" TEXT NOT NULL,
    "rdpPassword" TEXT NOT NULL,
    "rdpPort" INTEGER NOT NULL,

    CONSTRAINT "ChromePod_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserTraits" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT NOT NULL,

    CONSTRAINT "UserTraits_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Riasec" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "realistic" DOUBLE PRECISION NOT NULL,
    "investigative" DOUBLE PRECISION NOT NULL,
    "artistic" DOUBLE PRECISION NOT NULL,
    "social" DOUBLE PRECISION NOT NULL,
    "enterprising" DOUBLE PRECISION NOT NULL,
    "conventional" DOUBLE PRECISION NOT NULL,
    "summary" TEXT,
    "userTraitsId" TEXT NOT NULL,

    CONSTRAINT "Riasec_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MoralFoundations" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "careHarm" DOUBLE PRECISION NOT NULL,
    "fairnessCheating" DOUBLE PRECISION NOT NULL,
    "loyaltyBetrayal" DOUBLE PRECISION NOT NULL,
    "authoritySubversion" DOUBLE PRECISION NOT NULL,
    "sanctityDegradation" DOUBLE PRECISION NOT NULL,
    "summary" TEXT,
    "goodCheck" DOUBLE PRECISION NOT NULL,
    "mathCheck" DOUBLE PRECISION NOT NULL,
    "userTraitsId" TEXT NOT NULL,

    CONSTRAINT "MoralFoundations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PoliticalCompass" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "economic" DOUBLE PRECISION NOT NULL,
    "social" DOUBLE PRECISION NOT NULL,
    "summary" TEXT,
    "userTraitsId" TEXT NOT NULL,

    CONSTRAINT "PoliticalCompass_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BigFive" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "openness" DOUBLE PRECISION NOT NULL,
    "conscientiousness" DOUBLE PRECISION NOT NULL,
    "extraversion" DOUBLE PRECISION NOT NULL,
    "agreeableness" DOUBLE PRECISION NOT NULL,
    "neuroticism" DOUBLE PRECISION NOT NULL,
    "summary" TEXT,
    "userTraitsId" TEXT NOT NULL,

    CONSTRAINT "BigFive_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Mbti" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "extraversion" BOOLEAN NOT NULL,
    "sensing" BOOLEAN NOT NULL,
    "thinking" BOOLEAN NOT NULL,
    "judging" BOOLEAN NOT NULL,
    "summary" TEXT,
    "userTraitsId" TEXT NOT NULL,

    CONSTRAINT "Mbti_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SixteenPersonalityFactor" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "warmth" DOUBLE PRECISION NOT NULL,
    "reasoning" DOUBLE PRECISION NOT NULL,
    "emotionalStability" DOUBLE PRECISION NOT NULL,
    "dominance" DOUBLE PRECISION NOT NULL,
    "liveliness" DOUBLE PRECISION NOT NULL,
    "ruleConsciousness" DOUBLE PRECISION NOT NULL,
    "socialBoldness" DOUBLE PRECISION NOT NULL,
    "sensitivity" DOUBLE PRECISION NOT NULL,
    "vigilance" DOUBLE PRECISION NOT NULL,
    "abstractedness" DOUBLE PRECISION NOT NULL,
    "privateness" DOUBLE PRECISION NOT NULL,
    "apprehension" DOUBLE PRECISION NOT NULL,
    "opennessToChange" DOUBLE PRECISION NOT NULL,
    "selfReliance" DOUBLE PRECISION NOT NULL,
    "perfectionism" DOUBLE PRECISION NOT NULL,
    "tension" DOUBLE PRECISION NOT NULL,
    "summary" TEXT,
    "userTraitsId" TEXT NOT NULL,

    CONSTRAINT "SixteenPersonalityFactor_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserInterests" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT NOT NULL,

    CONSTRAINT "UserInterests_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterestsCluster" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "pipelineClusterId" INTEGER NOT NULL,
    "clusterType" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "activityDates" TEXT[],
    "isSensitive" BOOLEAN NOT NULL DEFAULT false,
    "userInterestsId" TEXT NOT NULL,

    CONSTRAINT "InterestsCluster_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterestsClusterMatch" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "interestsClusterId" TEXT NOT NULL,
    "interestsClustersSimilarityId" TEXT NOT NULL,

    CONSTRAINT "InterestsClusterMatch_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterestsClustersSimilarity" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "cosineSimilarity" DOUBLE PRECISION NOT NULL,
    "commonSummary" TEXT NOT NULL,

    CONSTRAINT "InterestsClustersSimilarity_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserMatch" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT NOT NULL,
    "usersOverallSimilarityId" TEXT NOT NULL,

    CONSTRAINT "UserMatch_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UsersOverallSimilarity" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "overallSimilarity" DOUBLE PRECISION NOT NULL,

    CONSTRAINT "UsersOverallSimilarity_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "User_displayName_key" ON "User"("displayName");

-- CreateIndex
CREATE UNIQUE INDEX "User_chromePodId_key" ON "User"("chromePodId");

-- CreateIndex
CREATE UNIQUE INDEX "Session_userId_key" ON "Session"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "ChromePod_chromePodId_key" ON "ChromePod"("chromePodId");

-- CreateIndex
CREATE UNIQUE INDEX "UserTraits_userId_key" ON "UserTraits"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "UserInterests_userId_key" ON "UserInterests"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "InterestsCluster_userInterestsId_pipelineClusterId_clusterT_key" ON "InterestsCluster"("userInterestsId", "pipelineClusterId", "clusterType");

-- CreateIndex
CREATE UNIQUE INDEX "InterestsClusterMatch_interestsClusterId_interestsClustersS_key" ON "InterestsClusterMatch"("interestsClusterId", "interestsClustersSimilarityId");

-- CreateIndex
CREATE UNIQUE INDEX "UserMatch_userId_usersOverallSimilarityId_key" ON "UserMatch"("userId", "usersOverallSimilarityId");

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_chromePodId_fkey" FOREIGN KEY ("chromePodId") REFERENCES "ChromePod"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Session" ADD CONSTRAINT "Session_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserTraits" ADD CONSTRAINT "UserTraits_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Riasec" ADD CONSTRAINT "Riasec_userTraitsId_fkey" FOREIGN KEY ("userTraitsId") REFERENCES "UserTraits"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MoralFoundations" ADD CONSTRAINT "MoralFoundations_userTraitsId_fkey" FOREIGN KEY ("userTraitsId") REFERENCES "UserTraits"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PoliticalCompass" ADD CONSTRAINT "PoliticalCompass_userTraitsId_fkey" FOREIGN KEY ("userTraitsId") REFERENCES "UserTraits"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BigFive" ADD CONSTRAINT "BigFive_userTraitsId_fkey" FOREIGN KEY ("userTraitsId") REFERENCES "UserTraits"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Mbti" ADD CONSTRAINT "Mbti_userTraitsId_fkey" FOREIGN KEY ("userTraitsId") REFERENCES "UserTraits"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SixteenPersonalityFactor" ADD CONSTRAINT "SixteenPersonalityFactor_userTraitsId_fkey" FOREIGN KEY ("userTraitsId") REFERENCES "UserTraits"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserInterests" ADD CONSTRAINT "UserInterests_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterestsCluster" ADD CONSTRAINT "InterestsCluster_userInterestsId_fkey" FOREIGN KEY ("userInterestsId") REFERENCES "UserInterests"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterestsClusterMatch" ADD CONSTRAINT "InterestsClusterMatch_interestsClusterId_fkey" FOREIGN KEY ("interestsClusterId") REFERENCES "InterestsCluster"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterestsClusterMatch" ADD CONSTRAINT "InterestsClusterMatch_interestsClustersSimilarityId_fkey" FOREIGN KEY ("interestsClustersSimilarityId") REFERENCES "InterestsClustersSimilarity"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserMatch" ADD CONSTRAINT "UserMatch_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserMatch" ADD CONSTRAINT "UserMatch_usersOverallSimilarityId_fkey" FOREIGN KEY ("usersOverallSimilarityId") REFERENCES "UsersOverallSimilarity"("id") ON DELETE CASCADE ON UPDATE CASCADE;
