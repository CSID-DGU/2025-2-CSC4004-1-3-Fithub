import prisma from "../../prisma";
import { repoService } from "./repoService";
import { treeService } from "./treeService";
import { commitService } from "./commitService";
import { issueService } from "./issueService";
import { pullService } from "./pullService";

export const snapshotService = {
  async createSnapshot(owner: string, repo: string, token: string) {
    console.log("Snapshot Start:", owner, repo);

    const repoInfo = await repoService.getRepoInfo(owner, repo, token);
    console.log("repoInfo.id =", repoInfo.id);
    const repoId = BigInt(repoInfo.id); 

    let savedRepo;
    try {
      console.log("repository upsert start");

      savedRepo = await prisma.repository.upsert({
        where: { repo_id: repoId },
        update: {},
        create: {
          repo_id: repoId,
          name: repoInfo.name,
          full_name: repoInfo.full_name,
          private: repoInfo.private,
          html_url: repoInfo.html_url,
          description: repoInfo.description,
          default_branch: repoInfo.default_branch,
          language: repoInfo.language,
          created_at: repoInfo.created_at ? new Date(repoInfo.created_at) : null,
          updated_at: repoInfo.updated_at ? new Date(repoInfo.updated_at) : null,
          pushed_at: repoInfo.pushed_at ? new Date(repoInfo.pushed_at) : null,
          owner_login: repoInfo.owner?.login || "",
        },
      });

      console.log("Repository successfully saved", savedRepo.repo_id);
    } catch (err) {
      console.error("Repository upsert failed", err);
      throw err; 
    }

    const tree = await treeService.getRepoTree(
      owner,
      repo,
      repoInfo.default_branch,
      token
    );
    console.log("Tree files:", tree?.tree?.length);

    await prisma.file.deleteMany({ where: { repo_id: savedRepo.repo_id } });

    if (tree.tree && Array.isArray(tree.tree)) {
      for (const f of tree.tree) {
        if (f.type === "blob") {
          await prisma.file.create({
            data: {
              repo_id: savedRepo.repo_id,
              path: f.path,
              sha: f.sha,
              size: f.size ?? null,
              type: f.type,
            },
          });
        }
      }
    }

    const commits = await commitService.getCommits(owner, repo, token);
    console.log("Commit count:", commits.length);

    await prisma.commit.deleteMany({ where: { repo_id: savedRepo.repo_id } });

    for (const c of commits) {
      await prisma.commit.create({
        data: {
          commit_sha: c.sha,
          repo_id: savedRepo.repo_id,
          author_name: c.commit?.author?.name || "",
          author_email: c.commit?.author?.email || "",
          date: c.commit?.author?.date ? new Date(c.commit.author.date) : null,
          message: c.commit?.message || "",
          parent_sha: c.parents?.[0]?.sha || null,
        },
      });
    }

    const issues = await issueService.getIssues(owner, repo, token);
    console.log("Issue count:", issues.length);

    await prisma.issue.deleteMany({ where: { repo_id: savedRepo.repo_id } });

    for (const issue of issues) {
      await prisma.issue.create({
        data: {
          issue_id: issue.id,
          repo_id: savedRepo.repo_id,
          title: issue.title,
          state: issue.state,
          created_at: issue.created_at ? new Date(issue.created_at) : null,
          closed_at: issue.closed_at ? new Date(issue.closed_at) : null,
        },
      });
    }

    const pulls = await pullService.getPullRequests(owner, repo, token);
    console.log("Pull Request count:", pulls.length);

    await prisma.pull.deleteMany({ where: { repo_id: savedRepo.repo_id } });

    for (const p of pulls) {
      await prisma.pull.create({
        data: {
          pull_id: p.id,
          repo_id: savedRepo.repo_id,
          title: p.title,
          state: p.state,
          created_at: p.created_at ? new Date(p.created_at) : null,
          closed_at: p.closed_at ? new Date(p.closed_at) : null,
        },
      });
    }
    console.log("Snapshot complete:", savedRepo.repo_id);
    return {
      repoId: savedRepo.repo_id.toString(),
      treeFiles: tree.tree?.length ?? 0,
      commits: commits.length,
      issues: issues.length,
      pulls: pulls.length,
    };
  },
};
