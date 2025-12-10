import axios from "axios";
import {
  repoService,
  treeService,
  commitService,
  issueService,
  pullService,
  fileService,
} from "./services";

const GITHUB_API = "https://api.github.com";

interface RepoSnapshotParams {
  owner: string;
  repo: string;
  token: string;
  branch?: string;
}

export async function getRepoSnapshot({
  owner,
  repo,
  token,
  branch,
}: RepoSnapshotParams) {
  const repoInfo = await repoService.getRepoInfo(owner, repo, token);
  const targetBranch = branch ?? repoInfo.default_branch ?? "main";

  const tree = await treeService.getRepoTree(owner, repo, targetBranch, token);
  const commits = await commitService.getCommits(owner, repo, token);
  const issues = await issueService.getIssues(owner, repo, token);
  const pulls = await pullService.getPullRequests(owner, repo, token);

  return {
    repoInfo,
    tree,
    commits,
    issues,
    pulls,
  };
}

export const getRepoInfo = repoService.getRepoInfo;
export const getCommits = commitService.getCommits;
export const getIssues = issueService.getIssues;
export const getPullRequests = pullService.getPullRequests;
export const getRepoTree = treeService.getRepoTree;
export const getFileContentSnapshot = fileService.getFileContent;

export const getRepoTreeAI = async (
  owner: string,
  repo: string,
  token: string
) => {
  const url = `${GITHUB_API}/repos/${owner}/${repo}/git/trees/main?recursive=1`;

  const res = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });

  return res.data.tree as Array<{ path: string; type: string }>;
};

export const getAllFiles = async (
  owner: string,
  repo: string,
  token: string
) => {
  const tree = await getRepoTreeAI(owner, repo, token);
  return tree.filter((item: { path: string; type: string }) => item.type === "blob");
};

export const getFileContent = async (
  owner: string,
  repo: string,
  path: string,
  token: string
) => {
  const url = `${GITHUB_API}/repos/${owner}/${repo}/contents/${path}`;

  const res = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });

  if (!res.data || !res.data.content) return null;

  return Buffer.from(res.data.content, "base64").toString("utf8");
};
