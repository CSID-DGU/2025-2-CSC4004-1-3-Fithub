import { Router, Request, Response, NextFunction } from "express";
import { githubDbController } from "../controller/githubDbController";
import { requireAuth,AuthRequest } from "../middleware/authMiddleware";
import { snapshotService } from "../github/services/snapshotService";
import prisma from "../prisma";

const router = Router();
// repo-snapshot
router.post(
  "/repo-snapshot",
  requireAuth,
  async (req: AuthRequest, res: Response, next: NextFunction) => {
    console.log("🔵 [DEBUG] /repo-snapshot route reached");

    try {
      console.log("📥 [DEBUG] Request Body:", req.body);
      console.log("🔐 [DEBUG] Authenticated User:", req.user);

      const { repoFullName } = req.body;

      // body validation
      if (!repoFullName) {
        console.error("❌ repoFullName missing in request body");
        return res.status(400).json({
          error: "repoFullName is required (format: 'owner/repo')",
        });
      }

      if (!repoFullName.includes("/")) {
        console.error("❌ repoFullName format incorrect:", repoFullName);
        return res.status(400).json({
          error: "repoFullName must be in 'owner/repo' format",
        });
      }

      const [owner, repo] = repoFullName.split("/");
      console.log(`🔍 [DEBUG] owner=${owner}, repo=${repo}`);

      const userId = req.user!.id;
      console.log("👤 [DEBUG] userId:", userId);

      const user = await prisma.user.findUnique({
        where: { id: userId },
        select: { githubAccessToken: true },
      });

      console.log("🔑 [DEBUG] Retrieved GitHub Token:", user?.githubAccessToken);

      if (!user?.githubAccessToken) {
        console.error("❌ No GitHub access token stored for user");
        return res.status(400).json({
          error: "User has no GitHub access token registered",
        });
      }

      console.log("🚀 [DEBUG] Calling snapshotService.createSnapshot...");
      const snapshot = await snapshotService.createSnapshot(
        owner,
        repo,
        user.githubAccessToken
      );

      console.log("✅ [DEBUG] Snapshot created successfully!");
      res.json(snapshot);

    } catch (err) {
      console.error("🔥 [ROUTE ERROR] /repo-snapshot:", err);
      next(err);
    }
  }
);


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
