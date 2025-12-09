import prisma from "../../prisma";
import { createGitHubClient } from "../client/githubClient";

export const dbService = {
  
  //repository
  async getRepo(repoId: string) {
    return prisma.repository.findUnique({
      where: { repo_id: BigInt(repoId) },
    });
  },

  //files
  async getRepoFiles(repoId: string) {
  return prisma.file.findMany({
    where: { repo_id: BigInt(repoId) },
    select: {
      path: true,
      content: true,   
    }
  });
},

  //file details
  async getFileDetail(repoId: string, filePath: string) {
  const repo = await prisma.repository.findUnique({
    where: { repo_id: BigInt(repoId) },
  });

    if (!repo) return null;
    const [owner, name] = repo.full_name!.split("/");
    const octokit = createGitHubClient(process.env.GITHUB_PERSONAL_TOKEN!);
    const response = await octokit.request(
     "GET /repos/{owner}/{repo}/contents/{path}",
     {
      owner,
      repo: name,
      path: filePath
     }
  );

  return response.data;
},
  //commits
  async getRepoCommits(repoId: string) {
    return prisma.commit.findMany({
      where: { repo_id: BigInt(repoId) },
      orderBy: { date: "desc" },
    });
  },

  async getCommitDetail(repoId: string, sha: string) {
    return prisma.commit.findFirst({
      where: {
        repo_id: BigInt(repoId),
        commit_sha: sha,
      },
    });
  },

  //issues
  async getRepoIssues(repoId: string) {
    return prisma.issue.findMany({
      where: { repo_id: BigInt(repoId) },
      orderBy: { created_at: "desc" },
    });
  },

 async getIssueDetail(repoId: string, issueId: string) {
  return prisma.issue.findFirst({
    where: {
      repo_id: BigInt(repoId),
      issue_id: BigInt(issueId),   // 수정
    },
  });
},

  //pull requests
  async getRepoPulls(repoId: string) {
    return prisma.pull.findMany({
      where: { repo_id: BigInt(repoId) },
      orderBy: { created_at: "desc" },
    });
  },

  async getPullDetail(repoId: string, pullId: string) {
  return prisma.pull.findFirst({
    where: {
      repo_id: BigInt(repoId),
      pull_id: BigInt(pullId),    // 수정
    },
  });
}

};
