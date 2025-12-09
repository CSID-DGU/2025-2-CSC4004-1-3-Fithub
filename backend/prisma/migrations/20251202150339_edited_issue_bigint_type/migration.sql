/*
  Warnings:

  - The primary key for the `issue` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The primary key for the `pull` table will be changed. If it partially fails, the table could be left without primary key constraint.

*/
-- DropForeignKey
ALTER TABLE "ProjectMember" DROP CONSTRAINT "ProjectMember_userId_fkey";

-- AlterTable
ALTER TABLE "issue" DROP CONSTRAINT "issue_pkey",
ALTER COLUMN "issue_id" SET DATA TYPE BIGINT,
ADD CONSTRAINT "issue_pkey" PRIMARY KEY ("issue_id");

-- AlterTable
ALTER TABLE "pull" DROP CONSTRAINT "pull_pkey",
ALTER COLUMN "pull_id" SET DATA TYPE BIGINT,
ADD CONSTRAINT "pull_pkey" PRIMARY KEY ("pull_id");

-- AddForeignKey
ALTER TABLE "ProjectMember" ADD CONSTRAINT "ProjectMember_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
