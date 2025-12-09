-- AddForeignKey
ALTER TABLE "Summary" ADD CONSTRAINT "Summary_repoId_fkey" FOREIGN KEY ("repoId") REFERENCES "repository"("repo_id") ON DELETE RESTRICT ON UPDATE CASCADE;
