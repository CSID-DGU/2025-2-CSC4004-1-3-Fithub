import { Request, Response, NextFunction } from "express";
import prisma from "../prisma";
import { AuthRequest } from "./authMiddleware";

//프로젝트 owner인지 여부 확인
export const requireProjectOwner = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  const userId = req.user?.id;
  const projectId = Number(req.params.projectId);

  if (!userId) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  //projectId 검증
  if (!projectId || isNaN(projectId)) {
    return res.status(400).json({ error: "Invalid or missing projectId in params" });
  }

  const project = await prisma.project.findUnique({
    where: { id: projectId },
  });

  if (!project) {
    return res.status(404).json({ error: "Project not found" });
  }

  if (project.ownerId !== userId) {
    return res.status(403).json({ error: "Only owner can modify members" });
  }

  next();
};


//프로젝트 멤버인지 여부 확인
export const requireProjectMember = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  const userId = req.user?.id;
  const projectId = Number(req.params.projectId);

  if (!userId) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  if (!projectId || isNaN(projectId)) {
    return res.status(400).json({ error: "Invalid or missing projectId in params" });
  }

  const membership = await prisma.projectMember.findFirst({
    where: { projectId, userId },
  });

  if (!membership) {
    return res.status(403).json({ error: "Not a project member" });
  }

  next();
};
