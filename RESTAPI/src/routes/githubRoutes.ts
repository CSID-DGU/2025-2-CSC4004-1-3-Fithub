// src/routes/githubRoutes.ts
import { Router, Request, Response, NextFunction } from "express";
import { getRepoSnapshot } from "../github/githubService";
import { requireGitHubToken, requireRepoFullName } from "../middleware/validateInput";

const router = Router();

router.post(
  "/repo-snapshot",
  requireGitHubToken,
  requireRepoFullName,
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const token = (req as any).githubToken as string;
      const owner = (req as any).owner as string;
      const repo = (req as any).repo as string;
      const branch = (req as any).branch as string | undefined;

      const snapshot = await getRepoSnapshot({
        token,
        owner,
        repo,
        branch
      });

      res.json(snapshot);
    } catch (err) {
      next(err);
    }
  }
);

export default router;
