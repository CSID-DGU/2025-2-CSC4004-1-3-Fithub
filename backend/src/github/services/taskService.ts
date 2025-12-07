import axios from "axios";
import prisma from "../../prisma";

const AI_SERVER = process.env.AI_SERVER;

// AI 서버 호출
export const requestAITasks = async (params: any) => {
  const response = await axios.post(`${AI_SERVER}/task`, params);
  return response.data.recommendations ?? response.data.tasks;
};

// DB 저장
export const saveTasks = async (tasksFromAI: any[]) => {
  const savedTasks = [];

  for (const t of tasksFromAI) {
    const saved = await prisma.task.create({
      data: {
        title: t.title ?? t.target ?? "AI Task",
        description: t.reason ?? t.description ?? "",
        projectId: t.projectId,
        repo_id: t.repoId ? BigInt(t.repoId) : null,
        role: t.role ?? null,
        source: "AI",
        runId: t.runId ?? null,
        target: t.target ?? null,
        priority: t.priority ?? null,
        taskType: t.type ?? null,
        category: t.category ?? null,
        confidence: t.confidence ?? null,
      },
    });

    savedTasks.push(saved);
  }

  return savedTasks;
};

// 역할별 조회
export const getTasksForUserRole = async (role: string) => {
  return prisma.task.findMany({
    where: { role: role as any },
  });
};

// 프로젝트별 조회
export const getTasksByProject = async (projectId: number) => {
  return prisma.task.findMany({
    where: { projectId },
  });
};
