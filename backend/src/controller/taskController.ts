// src/controller/taskController.ts

import { Request, Response } from "express";
import { taskService } from "../github/services/taskService";

export const getTasksByRunId = async (req: Request, res: Response) => {
  try {
    const { runId } = req.params;

    if (!runId) {
      return res.status(400).json({ error: "runId is required" });
    }

    const tasks = await taskService.getTasksByRunId(runId);
    return res.json({ runId, tasks });

  } catch (err: any) {
    console.error("[ERROR getTasksByRunId]", err.message);
    return res.status(500).json({ error: "Failed to fetch tasks" });
  }
};
