import { Response } from "express";
import prisma from "../prisma";
import { snapshotService } from "../github/services/snapshotService";
import { AuthRequest } from "../middleware/authMiddleware";

export async function repoSnapshotHandler(req: AuthRequest, res: Response) {
  try {
    const { repoFullName } = req.body;

    //body validation
    if (!repoFullName || !repoFullName.includes("/")) {
      return res.status(400).json({
        error: "repoFullName is required in format 'owner/repo'",
      });
    }

    const [owner, repo] = repoFullName.split("/");

    //logged-in user ID (from JWT)
    const userId = req.user!.id;

    //Fetch user's GitHub token from DB
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { githubAccessToken: true },
    });

    if (!user?.githubAccessToken) {
      return res.status(401).json({
        error: "GitHub access token missing. Please login via GitHub again.",
      });
    }

    const githubToken = user.githubAccessToken;

    //Snapshot 생성 (서비스 호출)
    const snapshot = await snapshotService.createSnapshot(
      owner,
      repo,
      githubToken
    );

    return res.json({
      message: "Snapshot created successfully",
      data: snapshot,
    });

  } catch (err: any) {
    console.error("[Snapshot Error]", err);
    return res.status(500).json({
      error: "INTERNAL_ERROR",
      message: err.message,
    });
  }
}
