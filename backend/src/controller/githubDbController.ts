import { Request, Response, NextFunction } from "express";
import { dbService } from "../github/services/dbService";
import { createGitHubClient } from "../github/client/githubClient";
import prisma from "../prisma";
import { AuthRequest } from "../middleware/authMiddleware";

export const githubDbController = {

  //get repository
  async getRepo(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId } = req.params;
      const repo = await dbService.getRepo(repoId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      return res.json(repo);
    } catch (error) {
      next(error);
    }
  },

  //get files
  async getRepoFiles(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId } = req.params;
      const files = await dbService.getRepoFiles(repoId);
      return res.json(files);
    } catch (error) {
      next(error);
    }
  },

  //get file details
  async getFileDetail(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId, fileId } = req.params;
      const file = await dbService.getFileDetail(repoId, fileId);

      if (!file) {
        return res.status(404).json({ message: "File not found" });
      }

      return res.json(file);
    } catch (error) {
      next(error);
    }
  },

  async getRepoFileTree(req: Request, res: Response, next: NextFunction) {
  try {
    const { repoId } = req.body; 

    if (!repoId) {
      return res.status(400).json({ message: "repoId is required" });
    }

    const repo = await dbService.getRepo(repoId);

    if (!repo) {
      return res.status(404).json({ message: "Repository not found" });
    }

    const [owner, repoNameRaw] = repo.full_name!.split("/");
    const repoName = repoNameRaw.replace(/\.git$/, "");

    const user = await prisma.user.findUnique({
      where: { id: req.user!.id },
      select: { githubAccessToken: true },
    });

    if (!user?.githubAccessToken) {
      return res.status(401).json({
        error: "GitHub access token missing. Please login again.",
      });
    }

    const octokit = createGitHubClient(user.githubAccessToken);

    //get tree SHA from branch
    const branchInfo = await octokit.request(
      "GET /repos/{owner}/{repo}/branches/{branch}",
      {
        owner,
        repo: repoName,
        branch: repo.default_branch || "main",
      }
    );

    const treeSha = branchInfo.data.commit.commit.tree.sha;

    //get filetree
    const tree = await octokit.request(
      "GET /repos/{owner}/{repo}/git/trees/{tree_sha}",
      {
        owner,
        repo: repoName,
        tree_sha: treeSha,
        recursive: "1",
      }
    );

    return res.json(tree.data);

  } catch (error) {
    next(error);
  }
},

  //get commits (DB 저장된 commit 목록)
  async getRepoCommits(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId } = req.params;
      const commits = await dbService.getRepoCommits(repoId);
      return res.json(commits);
    } catch (error) {
      next(error);
    }
  },

  //get commit details
  async getCommitDetail(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId, sha } = req.params;
      const commit = await dbService.getCommitDetail(repoId, sha);

      if (!commit) {
        return res.status(404).json({ message: "Commit not found" });
      }

      return res.json(commit);
    } catch (error) {
      next(error);
    }
  },

  //get issues (DB에 저장된 issue 목록)
  async getRepoIssues(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId } = req.params;
      const issues = await dbService.getRepoIssues(repoId);
      return res.json(issues);
    } catch (error) {
      next(error);
    }
  },

  //get issue details
  async getIssueDetail(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId, issueId } = req.params;
      const issue = await dbService.getIssueDetail(repoId, issueId);

      if (!issue) {
        return res.status(404).json({ message: "Issue not found" });
      }

      return res.json(issue);
    } catch (error) {
      next(error);
    }
  },

  //get pull requests (DB 저장된 pull 목록)
  async getRepoPulls(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId } = req.params;
      const pulls = await dbService.getRepoPulls(repoId);
      return res.json(pulls);
    } catch (error) {
      next(error);
    }
  },

  //get pull request details
  async getPullDetail(req: Request, res: Response, next: NextFunction) {
    try {
      const { repoId, pullId } = req.params;
      const pull = await dbService.getPullDetail(repoId, pullId);

      if (!pull) {
        return res.status(404).json({ message: "Pull request not found" });
      }

      return res.json(pull);
    } catch (error) {
      next(error);
    }
  },
};
