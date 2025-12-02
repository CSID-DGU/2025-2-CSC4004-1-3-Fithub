import { Router, Request, Response, NextFunction } from "express";
import { githubDbController } from "../controller/githubDbController";
import { requireAuth,AuthRequest } from "../middleware/authMiddleware";
import { snapshotService } from "../github/services/snapshotService";
import prisma from "../prisma";

const router = Router();

//repo-snapshot
router.post("/repo-snapshot", requireAuth, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { repoFullName } = req.body;

    if (!repoFullName || !repoFullName.includes("/")) {
      return res.status(400).json({
        error: "repoFullName must be 'owner/repo'",
      });
    }

    const [owner, repo] = repoFullName.split("/");

    const userId = req.user!.id;

    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { githubAccessToken: true }
    });

    if (!user?.githubAccessToken) {
      return res.status(400).json({
        error: "User has no GitHub access token registered"
      });
    }

    const snapshot = await snapshotService.createSnapshot(
      owner,
      repo,
      user.githubAccessToken
    );

    res.json(snapshot);

  } catch (err) {
    next(err);
  }
});

//Repos info
router.get("/repos/:repoId", githubDbController.getRepo);
router.get("/repos/:repoId/files/tree", githubDbController.getRepoFileTree);

//File tree
router.post("/repos/files/tree", requireAuth,githubDbController.getRepoFileTree);

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
