-- AlterTable
ALTER TABLE "issue" ADD COLUMN     "author" JSONB,
ADD COLUMN     "issue_number" INTEGER,
ADD COLUMN     "issue_url" TEXT;
