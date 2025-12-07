import prisma from "../../prisma";
import { Role } from "@prisma/client";

//프로젝트 생성
export const createProject = async (data: any) => {
  const { name, description, ownerId } = data;

  const project = await prisma.project.create({
    data: {
      name,
      description,
      ownerId,
    },
  });
  return project;
};

//프로젝트 목록 조회
export const getProjectLists = async () => {
  return prisma.project.findMany({
    orderBy: { createdAt: "desc" },
  });
};

//프로젝트 상세정보 조회
export const getProjectById = async (projectId: number) => {
  return prisma.project.findUnique({
    where: { id: projectId },
    include: {
      owner: true,
      repos: {
        include: {
          repo: true, 
        },
      },
      members: {
        include: {
          user: true, 
        },
      },
    },
  });
};

//프로젝트에 github 레포지토리 추가
export const addRepoToProject = async (
  projectId: number,
  githubRepo: {
    id: bigint;
    name: string;
    full_name: string;
    html_url: string;
  }
) => {

  const repo = await prisma.repository.upsert({
    where: { repo_id: githubRepo.id },
    update: {},
    create: {
      repo_id: githubRepo.id,
      name: githubRepo.name,
      full_name: githubRepo.full_name,
      html_url: githubRepo.html_url,
    },
  });

  const projectRepo = await prisma.projectRepository.create({
    data: {
      projectId,
      repo_id: repo.repo_id,
    },
  });

  return projectRepo;
};

//프로젝트 멤버 추가
export const addMemberToProject = async (projectId: number, userId: number) => {
  return prisma.projectMember.create({
    data: {
      projectId,
      userId,
    },
  });
};

//프로젝트 삭제
export const deleteProject = async (projectId: number) => {
  // 프로젝트 존재 여부 확인
  const project = await prisma.project.findUnique({
    where: { id: projectId },
  });

  if (!project) return null;

  // 👉 1) projectRepository 먼저 삭제
  await prisma.projectRepository.deleteMany({
    where: { projectId },
  });

  // 👉 2) projectMember 삭제 (이게 없으면 FK 에러 터짐)
  await prisma.projectMember.deleteMany({
    where: { projectId },
  });

  // 👉 3) 프로젝트 삭제
  await prisma.project.delete({
    where: { id: projectId },
  });

  return true;
};


//프로젝트 멤버 조회
export const getProjectMembers = async (projectId: number) => {
  return prisma.projectMember.findMany({
    where: { projectId },
    include: {
      user: true, 
    },
  });
};

//프로젝트 멤버 삭제
export const removeProjectMember = async (projectId: number, userId: number) => {
  return prisma.projectMember.deleteMany({
    where: {
      projectId,
      userId,
    },
  });
};

//프로젝트 역할 
export const getRoles = ()=>{
  return[
    "FRONTEND",
    "BACKEND",
    "AI",
    "DEVOPS",
    "DATABASE",
    "COMMON"
  ];
}

//프로젝트 멤버 역할 업데이트(배정,수정)
export const updateProjectMemberRole = async (
  projectId: number,
  memberId: number,
  role: string
) => {
  const member = await prisma.projectMember.findUnique({
    where: { id: memberId },
  });

  if (!member) {
    throw new Error("Project member not found");
  }

  const updated = await prisma.projectMember.update({
    where: { id: memberId },
    data: { role: role as any },
  });

  return updated;
};

//프로젝트 멤버 역할 삭제 
export const removeRoleFromMember = async (
  projectId: number,
  userId: number,
  role: string
) => {
  
  //ProjectMember 존재 여부 확인
  const member = await prisma.projectMember.findFirst({
    where: {
      projectId,
      userId,
      role: role as Role,
    }
  });

  if (!member) return null;

  await prisma.projectMember.delete({
    where: {
      id: member.id, 
    }
  });

  return true;
};
