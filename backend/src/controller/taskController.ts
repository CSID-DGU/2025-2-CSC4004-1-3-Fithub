import { Request, Response } from "express";
import prisma from "../prisma";
import {
  requestAITasks,
  saveTasks,
  getTasksByProject,
} from "../github/services/taskService";

interface AuthRequest extends Request {
  user?: {
    id: number;
    role?: string;
    github_id?: number;
    username?: string;
  };
}

//generate Tasks
export const generateTasks = async (req: Request, res: Response) => {
  try {
    const aiParams = req.body;

    const tasksFromAI = await requestAITasks(aiParams);
    const savedTasks = await saveTasks(tasksFromAI);

    res.json({
      message: "Tasks generated successfully",
      tasks: savedTasks,
    });
  } catch (err) {
    console.error("Task generation error:", err);
    res.status(500).json({ error: "Failed to generate tasks" });
  }
};

export const getTasksByProjectController = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    const tasks = await getTasksByProject(projectId);

    res.json(tasks);
  } catch (err) {
    console.error("Get project tasks error:", err);
    res.status(500).json({ error: "Failed to get tasks for project" });
  }
};

export const getTasksByMyRole = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const projectId = Number(req.params.projectId);

    const member = await prisma.projectMember.findFirst({
      where: { userId, projectId },
    });

    if (!member || !member.role_id) {
      return res.status(400).json({ error: "No role assigned in this project" });
    }

    const tasks = await prisma.task.findMany({
      where: {
        projectId,
        role_id: member.role_id,
      },
    });

    res.json(tasks);
  } catch (err) {
    console.error("Task recommendation error:", err);
    res.status(500).json({ error: "Failed to get tasks by my role" });
  }
};
