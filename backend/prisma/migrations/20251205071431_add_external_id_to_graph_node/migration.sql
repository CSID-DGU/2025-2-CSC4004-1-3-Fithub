/*
  Warnings:

  - You are about to drop the column `file_path` on the `GraphNode` table. All the data in the column will be lost.
  - Added the required column `external_id` to the `GraphNode` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "GraphNode" DROP COLUMN "file_path",
ADD COLUMN     "external_id" TEXT NOT NULL,
ADD COLUMN     "parent_id" TEXT;
