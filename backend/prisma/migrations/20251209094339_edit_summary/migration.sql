/*
  Warnings:

  - You are about to drop the column `content` on the `Summary` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "Summary" DROP COLUMN "content";

-- CreateTable
CREATE TABLE "SummaryItem" (
    "id" SERIAL NOT NULL,
    "summaryId" INTEGER NOT NULL,
    "codeId" TEXT,
    "text" TEXT,
    "unifiedSummary" TEXT,
    "level" TEXT,
    "qualityScore" DOUBLE PRECISION,
    "logic" TEXT,
    "intent" TEXT,
    "structure" TEXT,

    CONSTRAINT "SummaryItem_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "SummaryItem" ADD CONSTRAINT "SummaryItem_summaryId_fkey" FOREIGN KEY ("summaryId") REFERENCES "Summary"("id") ON DELETE CASCADE ON UPDATE CASCADE;
