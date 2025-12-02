import prisma from "../../prisma";

//create Project
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

//get Project info
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


// add repository to Project
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

//add member to Project
export const addMemberToProject = async (projectId: number, userId: number) => {
  return prisma.projectMember.create({
    data: {
      projectId,
      userId,
    },
  });
};

//get Proejct Members
export const getProjectMembers = async (projectId: number) => {
  return prisma.projectMember.findMany({
    where: { projectId },
    include: {
      user: true, 
    },
  });
};

//delete Project Members
export const removeProjectMember = async (projectId: number, userId: number) => {
  return prisma.projectMember.deleteMany({
    where: {
      projectId,
      userId,
    },
  });
};

//get role list(Enum type)
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

//update Project Member roles
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
