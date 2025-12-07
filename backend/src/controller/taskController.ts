import { Request, Response } from "express";
import prisma from "../prisma";
import {
  requestAITasks,
  saveTasks,
  getTasksByProject,
  getTasksForUserRole
} from "../github/services/taskService";

interface AuthRequest extends Request {
  user?: {
    id: number;
  };
}

// AI 태스크 생성
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

// 프로젝트 단위 조회
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

// 내 역할 기반 조회
export const getTasksByMyRole = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const projectId = Number(req.params.projectId);

    const member = await prisma.projectMember.findFirst({
      where: { userId, projectId },
    });

    if (!member || !member.role) {
      return res.status(400).json({ error: "No role assigned in this project" });
    }

    const tasks = await getTasksForUserRole(member.role);
    res.json(tasks);
  } catch (err) {
    console.error("Task recommendation error:", err);
    res.status(500).json({ error: "Failed to get tasks by my role" });
  }
};
