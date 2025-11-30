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


//aod repository to Project
export const addRepoToProject = async (projectId: number, repoId: bigint) => {
  const projectRepo = await prisma.projectRepository.create({
    data: {
      projectId,
      repo_id: repoId,
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
