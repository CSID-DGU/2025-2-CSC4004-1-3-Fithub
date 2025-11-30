//get repository, file(+tree), commit, issue, pull request and details
import { Request, Response, NextFunction } from "express";
import { dbService } from "../github/services/dbService";
import { createGitHubClient } from "../github/client/githubClient";

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

  //get file tree
  async getRepoFileTree(req: Request, res: Response, next: NextFunction) {
  try {
    const { repoId } = req.params;
    const repo = await dbService.getRepo(repoId);
    if (!repo) {
      return res.status(404).json({ message: "Repository not found" });
    }

    const [owner, repoName] = repo.full_name!.split("/");

    const token = process.env.GITHUB_PERSONAL_TOKEN!;
    const octokit = createGitHubClient(token);

    const tree = await octokit.request(
      "GET /repos/{owner}/{repo}/git/trees/{branch}",
      {
        owner,
        repo: repoName,
        branch: repo.default_branch || "main",
        recursive: "1",
      }
    );
    
    return res.json(tree.data);

  } catch (error) {
    next(error);
  }
},

  //get commits
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

  //get issues
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

  //get pull requests
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
