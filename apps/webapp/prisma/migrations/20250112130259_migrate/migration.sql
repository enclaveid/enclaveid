-- CreateEnum
CREATE TYPE "NodeType" AS ENUM ('Observable', 'Inferrable', 'Speculative');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "WhitelistedEmail" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "WhitelistedEmail_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserClaim" (
    "id" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "nodeType" "NodeType" NOT NULL,
    "conversationId" TEXT NOT NULL,
    "frequency" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "claimCategoryId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,

    CONSTRAINT "UserClaim_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ClaimCategory" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "clusterLabel" INTEGER NOT NULL,
    "isPersonal" BOOLEAN NOT NULL,

    CONSTRAINT "ClaimCategory_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "WhitelistedEmail_email_key" ON "WhitelistedEmail"("email");

-- AddForeignKey
ALTER TABLE "UserClaim" ADD CONSTRAINT "UserClaim_claimCategoryId_fkey" FOREIGN KEY ("claimCategoryId") REFERENCES "ClaimCategory"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserClaim" ADD CONSTRAINT "UserClaim_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
