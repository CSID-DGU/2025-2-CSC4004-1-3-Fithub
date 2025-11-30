//get repository snapshot
import { Request, Response } from "express";
import { snapshotService } from "../github/services/snapshotService";

//repository snapshot
export async function repoSnapshotHandler(req: Request, res: Response) {
  try {
    const { token, repo } = req.body;

    if (!token || !repo) {
      return res.status(400).json({
        error: "token and repo are required.",
      });
    }

    const [owner, repoName] = repo.split("/");
    if (!owner || !repoName) {
      return res.status(400).json({
        error: "Repo must be in 'owner/repoName' format.",
      });
    }

    const result = await snapshotService.createSnapshot(owner, repoName, token);

    res.json({
      message: "Snapshot created successfully.",
      data: result,
    });
  } 
  
  catch (err: any) {
    console.error("Snapshot Error:", err);
    res.status(500).json({
      error: "Failed to create snapshot.",
      detail: err.message,
    });
  }
}
