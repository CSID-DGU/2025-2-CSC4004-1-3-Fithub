/*
  Warnings:

  - A unique constraint covering the columns `[runId]` on the table `Summary` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `runId` to the `Summary` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "Summary" DROP CONSTRAINT "Summary_repoId_fkey";

-- AlterTable
ALTER TABLE "Summary" ADD COLUMN     "runId" TEXT NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "Summary_runId_key" ON "Summary"("runId");
