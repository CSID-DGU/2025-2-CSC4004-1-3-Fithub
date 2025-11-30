import { Request, Response } from "express";
import {
  generateAndSaveGraph,
  getGraphByRepoId,
} from "../github/services/aiGraphService";

export const createGraphController = async (req: Request, res: Response) => {
  try {
    const { repoId, summaries, embeddings, contextMeta } = req.body;

    if (!repoId || !summaries || !embeddings) {
      return res.status(400).json({
        error: "repoId, summaries, embeddings are required",
      });
    }

    const result = await generateAndSaveGraph(BigInt(repoId), {
      summaries,
      embeddings,
      contextMeta,
    });

    res.json(result);
  } catch (err: any) {
    console.error("Graph generation error:", err);
    res.status(500).json({ error: "Graph generation failed" });
  }
};

export const getGraphController = async (req: Request, res: Response) => {
  try {
    const repoId = BigInt(req.params.repoId);

    const graph = await getGraphByRepoId(repoId);
    res.json(graph);
  } catch (err: any) {
    console.error("Graph fetch error:", err);
    res.status(500).json({ error: "Graph fetch failed" });
  }
};
