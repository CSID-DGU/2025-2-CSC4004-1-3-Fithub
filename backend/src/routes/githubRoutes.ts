import { Router, Request, Response, NextFunction } from "express";
import { requireGitHubToken, requireRepoFullName } from "../middleware/validateInput";
import { snapshotService } from "../github/services/snapshotService";
import { githubDbController } from "../controller/githubDbController";

const router = Router();

// Snapshot
router.post(
  "/repo-snapshot",
  requireGitHubToken,
  requireRepoFullName,
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const token = (req as any).githubToken as string;
      const owner = (req as any).owner as string;
      const repo = (req as any).repo as string;

      const snapshot = await snapshotService.createSnapshot(owner, repo, token);
      res.json(snapshot);
    } catch (err) {
      next(err);
    }
  }
);

// Repos
router.get("/repos/:repoId", githubDbController.getRepo);
router.get("/repos/:repoId/files/tree", githubDbController.getRepoFileTree);

//File list
router.get("/repos/:repoId/files", githubDbController.getRepoFiles);

//File detail
router.get("/repos/:repoId/files/:fileId", githubDbController.getFileDetail);

//Commits
router.get("/repos/:repoId/commits", githubDbController.getRepoCommits);
router.get("/repos/:repoId/commits/:sha", githubDbController.getCommitDetail);

//Issues
router.get("/repos/:repoId/issues", githubDbController.getRepoIssues);
router.get("/repos/:repoId/issues/:issueId", githubDbController.getIssueDetail);

//Pull Requests
router.get("/repos/:repoId/pulls", githubDbController.getRepoPulls);
router.get("/repos/:repoId/pulls/:pullId", githubDbController.getPullDetail);

export default router;
