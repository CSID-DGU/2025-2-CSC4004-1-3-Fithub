import { createGitHubClient } from "./githubClient";

export interface RepoSnapshotInput {
  token: string;
  owner: string;
  repo: string;
  branch?: string;
}

export async function getRepoSnapshot(input: RepoSnapshotInput) {
  const { token, owner, repo, branch } = input;

  const octokit = createGitHubClient(token);

  const repoResp = await octokit.rest.repos.get({ owner, repo });
  const repoData = repoResp.data;

  const branchName = branch ?? repoData.default_branch;

  const branchResp = await octokit.rest.repos.getBranch({
    owner,
    repo,
    branch: branchName
  });
  const branchData = branchResp.data;

  const treeSha = branchData.commit.commit.tree.sha;

  const treeResp = await octokit.rest.git.getTree({
    owner,
    repo,
    tree_sha: treeSha,
    recursive: "1"
  });
  const treeData = treeResp.data;

  return {
    repository: {
      id: repoData.id,
      full_name: repoData.full_name,
      default_branch: repoData.default_branch,
      private: repoData.private,
      html_url: repoData.html_url,
      description: repoData.description,
      language: repoData.language,
      pushed_at: repoData.pushed_at,
      raw: repoData
    },
    branch: {
      name: branchData.name,
      commit_sha: branchData.commit.sha,
      tree_sha: treeSha,
      protected: branchData.protected,
      raw: branchData
    },
    tree: {
      truncated: treeData.truncated,
      sha: treeData.sha,
      raw: treeData
    }
  };
}
