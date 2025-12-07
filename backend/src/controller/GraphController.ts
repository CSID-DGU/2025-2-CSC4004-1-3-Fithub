import { Request, Response } from "express";
import { saveGraphToDB, getGraphByRepoId } from "../github/services/GraphService";

export const uploadGraph = async (req: Request, res: Response) => {
  try {
    const { repoId, graph } = req.body;

    if (!repoId) {
      return res.status(400).json({ error: "repoId is required" });
    }
    if (!graph || !graph.nodes || !graph.edges) {
      return res.status(400).json({ error: "graph (nodes + edges) is required" });
    }

    const result = await saveGraphToDB(BigInt(repoId), graph);
    return res.json(result);
  } catch (err: any) {
    console.error("uploadGraph error:", err);
    return res.status(500).json({
      error: "Failed to save graph",
      details: err.message,
    });
  }
};

export const fetchGraph = async (req: Request, res: Response) => {
  try {
    const { repoId } = req.params;

    if (!repoId) {
      return res.status(400).json({ error: "repoId param is required" });
    }

    const graphData = await getGraphByRepoId(BigInt(repoId));
    return res.json(graphData);
  } catch (err: any) {
    console.error("fetchGraph error:", err);
    return res.status(500).json({
      error: "Failed to fetch graph",
      details: err.message,
    });
  }
};
