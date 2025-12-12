import axios from "axios";
import { Request, Response } from "express";
import { recommendationService } from "../github/services/recommendationService";

const AI_AGENT_URL = process.env.AI_AGENT_URL || "http://localhost:8000";

// 분석 시작
export const startFullAnalysis = async (req: Request, res: Response) => {
  console.log("START ANALYSIS");

  try {
    const { repo } = req.body;

    if (!repo?.repo_id) {
      return res.status(400).json({ error: "repo.repo_id is required" });
    }

    const analyzeRes = await axios.post(`${AI_AGENT_URL}/analyze`, { repo });
    const runId = analyzeRes.data.run_id;

    console.log("[RUN START] runId =", runId);

    return res.json({ runId });

  } catch (err: any) {
    console.error("ERROR startFullAnalysis:", err.message);
    return res.status(500).json({ error: "Failed to start analysis" });
  }
};


// 분석 상태 체크
export const getAnalysisStatus = async (req: Request, res: Response) => {
  console.log("CHECK STATUS");

  try {
    const { runId } = req.params;

    const aiRes = await axios.get(`${AI_AGENT_URL}/result/${runId}`);
    const aiData = aiRes.data;

    console.log("[STATUS CHECK] agent status =", aiData.status);

    if (aiData.status === "completed") {
      return res.json({ status: "completed" });
    }

    return res.json({ status: "processing" });

  } catch (err) {
    console.error("ERROR getAnalysisStatus:", (err as any).message);
    return res.json({ status: "processing" });
  }
};


// 분석 결과 조회
export const getAnalysisResult = async (req: Request, res: Response) => {
  console.log("LOAD RESULT (GRAPH: RAW, RECO: SAVE)");

  try {
    const { runId } = req.params;
    const { repoId } = req.query;

    if (!repoId) {
      return res.status(400).json({ error: "repoId is required in query" });
    }

    const repoIdBigInt = BigInt(repoId as string);

    console.log("[AI REQUEST] GET /result/" + runId);

    const aiRes = await axios.get(`${AI_AGENT_URL}/result/${runId}`);
    const aiData = aiRes.data;

    console.log("[AI RESPONSE STATUS]", aiData.status);

    if (aiData.status !== "completed") {
      return res.json({ status: "processing" });
    }

    const result = aiData.result;

    if (!result) {
      return res.json({ status: "processing", message: "Result not ready" });
    }

    if (Array.isArray(result.recommendations)) {
      console.log("[RECOMMENDATION SAVE]");
      await recommendationService.saveRecommendations(
        runId,
        repoIdBigInt,
        result.recommendations
      );
    }

    console.log("[RETURN RAW GRAPH + RECOMMENDATIONS]");

    return res.json({
      runId,
      status: "completed",
      graph: result.graph,             
      recommendations: result.recommendations || []
    });

  } catch (err: any) {
    console.error("ERROR getAnalysisResult:", err.message);
    return res.status(500).json({
      error: "Failed to load result",
      details: err.message
    });
  }
};
