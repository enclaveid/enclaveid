-- AlterTable
ALTER TABLE "ApiKey" ALTER COLUMN "key" SET DEFAULT encode(sha256(random()::text::bytea), 'hex');

-- CreateTable
CREATE TABLE "MessagingPartner" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "phoneNumber" TEXT NOT NULL,
    "numberOfMessages" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT NOT NULL,

    CONSTRAINT "MessagingPartner_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "MessagingPartner" ADD CONSTRAINT "MessagingPartner_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
