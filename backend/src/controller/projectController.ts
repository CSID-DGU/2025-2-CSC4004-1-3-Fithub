import { Request, Response } from "express";
import * as projectService from "../github/services/projectService";
import { AuthRequest } from "../middleware/authMiddleware";
import prisma from "../prisma";
import * as githubService from "../github/githubService";
import { Role } from "@prisma/client"; 

//프로젝트 생성
export const createProject = async (req: AuthRequest, res: Response) => {
  try {
    const { name, description } = req.body;
    const ownerId = req.user!.id;

    const project = await prisma.project.create({
      data: {
        name,
        description,
        ownerId,
      },
    });

    res.json(project);
  } catch (err) {
    console.error("Create project error:", err);
    res.status(500).json({ error: "Failed to create project" });
  }
};

//프로젝트 상세정보 조회
export const getProjectById = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);

    const project = await prisma.project.findUnique({
      where: { id: projectId },
      include: {
        members: true,
        repos: true,
      },
    });

    if (!project) return res.status(404).json({ error: "Project not found" });

    res.json(project);
  } catch (err) {
    console.error("Get project error:", err);
    res.status(500).json({ error: "Failed to load project" });
  }
};

//프로젝트에 github repository 추가
export const addRepoToProject = async (req: Request, res: Response) => {
  try {
    const { owner, repo, token } = req.body;
    const projectId = Number(req.params.projectId);

    const githubRepo = await githubService.getRepoInfo(owner, repo, token);

    const result = await projectService.addRepoToProject(projectId, {
      id: BigInt(githubRepo.id),
      name: githubRepo.name,
      full_name: githubRepo.full_name,
      html_url: githubRepo.html_url,
    });

    res.json(result);

  } catch (err: any) {
    console.error("Add repo error:", err);

    //GitHub 404 (repo 없음)
    if (err.status === 404) {
      return res.status(404).json({
        error: "GitHub repository not found"
      });
    }

    //GitHub 인증 실패 (토큰 문제)
    if (err.status === 401) {
      return res.status(401).json({
        error: "Unauthorized: Invalid GitHub token"
      });
    }

    //GitHub rate limit / API 문제
    if (err.status === 403 || err.status === 429) {
      return res.status(429).json({
        error: "GitHub API rate limit exceeded"
      });
    }

    //요청 자체가 잘못된 경우 (owner/repo 누락)
    if (err instanceof TypeError || err.message?.includes("undefined")) {
      return res.status(400).json({
        error: "Bad Request: owner, repo, and token are required"
      });
    }
    
    //기타
    res.status(500).json({
      error: "Internal Server Error"
    });
  }
};

//프로젝트 리스트 조회:callback 오류가 반복적으로 발생하여 routes에서 직접 callback

//프로젝트 삭제
export const deleteProject = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);

    if (!projectId || isNaN(projectId)) {
      return res.status(400).json({ error: "Invalid projectId" });
    }

    const deleted = await projectService.deleteProject(projectId);

    if (!deleted) {
      return res.status(404).json({ error: "Project not found" });
    }

    return res.status(200).json({
      message: "Project deleted successfully",
      projectId: projectId
    });

  } catch (err) {
    console.error("Delete Project Error:", err);
    return res.status(500).json({ error: "Failed to delete project" });
  }
};


//프로젝트 멤버 추가
export const addProjectMember = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    const { userId } = req.body;

    const member = await prisma.projectMember.create({
      data: {
        projectId,
        userId,
      },
    });

    res.json(member);
  } catch (err) {
    console.error("Add member error:", err);
    res.status(500).json({ error: "Failed to add member" });
  }
};

//프로젝트 멤버 조회
export const getProjectMembers = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);

    const members = await prisma.projectMember.findMany({
      where: { projectId },
      include: { user: true },
    });

    res.json(members);
  } catch (err) {
    console.error("Get members error:", err);
    res.status(500).json({ error: "Failed to retrieve members" });
  }
};

//프로젝트 멤버 삭제
export const removeProjectMember = async (req: Request, res: Response) => {
  try {
    const memberId = Number(req.params.userId); 

    await prisma.projectMember.delete({
      where: { id: memberId },
    });

    res.json({ message: "Member removed" });
  } catch (err) {
    console.error("Remove member error:", err);
    res.status(500).json({ error: "Failed to remove member" });
  }
};

//프로젝트 멤버 역할 조회
export const getUserRoles = async (req: Request, res: Response) => {
  try {
    const roles = Object.values(Role); 
    res.json(roles);
  } catch (err) {
    console.error("Get roles error:", err);
    res.status(500).json({ error: "Failed to load roles" });
  }
};

//프로젝트 멤버 역할 업데이트(배정,수정)
export const updateProjectMemberRole = async (req: Request, res: Response) => {
  try {
    const memberId = Number(req.params.memberId);
    const { role } = req.body;

    const updated = await prisma.projectMember.update({
      where: { id: memberId },
      data: { role },
    });

    res.json(updated);
  } catch (err) {
    console.error("Update role error:", err);
    res.status(500).json({ error: "Failed to update role" });
  }
};

//프로젝트 멤버 역할 제거
export const removeRole = async (req: Request, res: Response) => {
  try {
    const projectId = Number(req.params.projectId);
    const userId = Number(req.params.userId);
    const role = req.params.role;

    if (!projectId || isNaN(projectId)) {
      return res.status(400).json({ error: "Invalid projectId" });
    }
    if (!userId || isNaN(userId)) {
      return res.status(400).json({ error: "Invalid userId" });
    }
    if (!role) {
      return res.status(400).json({ error: "Invalid role" });
    }

    const deleted = await projectService.removeRoleFromMember(
      projectId,
      userId,
      role
    );

    if (!deleted) {
      return res.status(404).json({
        error: "Role not found for this user in this project",
      });
    }

    return res.status(200).json({
      message: "Role removed successfully",
      projectId,
      userId,
      role,
    });
  } catch (err) {
    console.error("Remove role error:", err);
    return res
      .status(500)
      .json({ error: "Failed to remove role from project member" });
  }
};
