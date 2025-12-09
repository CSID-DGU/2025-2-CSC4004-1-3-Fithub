import axios from "axios";
import fs from "fs";
import path from "path";
import { Request, Response } from "express";

import { summaryService } from "../github/services/summaryService";
import { taskService } from "../github/services/taskService";

const AI_AGENT_URL = process.env.AI_AGENT_URL || "http://localhost:8000";

const runRepoMap = new Map<string, bigint>();
const runProjectMap = new Map<string, number>();
const analysisStatus = new Map<string, string>();


//POST /analysis/run
export const startFullAnalysis = async (req: Request, res: Response) => {
  console.log("=== [START ANALYSIS] ===");
  console.log("Request body:", req.body);

  try {
    const { repo, projectId } = req.body;

    if (!repo || !repo.repo_id) {
      console.error("[ERROR] Missing repo.repo_id");
      return res.status(400).json({ error: "repo.repo_id is required" });
    }
    if (!projectId) {
      console.error("[ERROR] Missing projectId");
      return res.status(400).json({ error: "projectId is required" });
    }

    const repoId = BigInt(repo.repo_id);
    console.log(`→ repoId: ${repoId}, projectId: ${projectId}`);

    console.log(`→ Sending request to AI agent: ${AI_AGENT_URL}/analyze`);

    const analyzeRes = await axios.post(`${AI_AGENT_URL}/analyze`, { repo });

    const runId = analyzeRes.data.run_id;
    console.log(`→ AI returned runId: ${runId}`);

    runRepoMap.set(runId, repoId);
    runProjectMap.set(runId, projectId);
    analysisStatus.set(runId, "processing");

    console.log("=== [START ANALYSIS COMPLETE] ===");

    return res.json({ runId });

  } catch (err: any) {
    console.error("[ERROR startFullAnalysis]");
    console.error("Message:", err.message);
    console.error("Stack:", err.stack);
    return res.status(500).json({ error: "Failed to start analysis" });
  }
};



//GET /analysis/status/:runId
export const getAnalysisStatus = async (req: Request, res: Response) => {
  console.log("=== [CHECK STATUS] ===");

  try {
    const { runId } = req.params;

    const baseDir = path.join(__dirname, "../../results", runId);
    console.log(`→ Checking directory: ${baseDir}`);

    if (fs.existsSync(baseDir)) {
      console.log("→ Status: completed");
      analysisStatus.set(runId, "completed");
      return res.json({ status: "completed" });
    }

    console.log("→ Status: processing");
    return res.json({ status: "processing" });

  } catch (err: any) {
    console.error("[ERROR getAnalysisStatus]");
    console.error("Message:", err.message);
    console.error("Stack:", err.stack);
    return res.status(500).json({ error: "Failed to check status" });
  }
};



//GET /analysis/result/:runId -> structural.json(graph), summary & task (db 파싱된 버전) 조회
export const getAnalysisResult = async (req: Request, res: Response) => {
  console.log("=== [LOAD ANALYSIS RESULT] ===");

  try {
    const { runId } = req.params;

    const repoId = runRepoMap.get(runId);
    const projectId = runProjectMap.get(runId);

    console.log(`→ runId: ${runId}`);
    console.log(`→ repoId: ${repoId}, projectId: ${projectId}`);

    if (!repoId || !projectId) {
      console.error("Invalid runId mapping — repoId or projectId missing");
      return res.status(400).json({ error: "Invalid runId mapping" });
    }

    const baseDir = path.join(__dirname, "../../results", runId);
    console.log(`→ Looking for result folder: ${baseDir}`);

    if (!fs.existsSync(baseDir)) {
      console.error("Result folder not found");
      return res.status(404).json({ error: "Result not ready" });
    }



    //structural.json
    console.log("→ Reading structural.json...");
    const structuralPath = path.join(baseDir, "structural.json");
    let structural = null;

    if (fs.existsSync(structuralPath)) {
      try {
        structural = JSON.parse(fs.readFileSync(structuralPath, "utf-8"));
        console.log("structural.json loaded");
      } catch (err) {
        console.error("Failed parsing structural.json");
        console.error(err);
      }
    } else {
      console.warn("structural.json NOT found");
    }



    //Save summary from summarization.json
    console.log("→ Saving summary into DB...");
    try {
      await summaryService.saveSummaryFromResult(runId, repoId);
      console.log("Summary saved");
    } catch (err) {
      console.error("ERROR saving summary");
      console.error(err);
    }

    const summary = await summaryService.getSummaryByRunId(runId);



    //Save tasks from task_output.json
    console.log("→ Saving tasks into DB...");
    try {
      await taskService.saveTasksFromResult(runId, repoId, projectId);
      console.log("Tasks saved");
    } catch (err) {
      console.error("ERROR saving tasks");
      console.error(err);
    }

    const tasks = await taskService.getTasksByRunId(runId);


    console.log("=== [RESULT READY → RETURNING JSON] ===");

    return res.json({
      runId,
      structural,
      summary,
      tasks
    });

  } catch (err: any) {
    console.error("[ERROR getAnalysisResult]");
    console.error("Message:", err.message);
    console.error("Stack:", err.stack);
    return res.status(500).json({ error: "Failed to load analysis result" });
  }
};
