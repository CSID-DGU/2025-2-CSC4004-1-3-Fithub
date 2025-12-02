import { createGitHubClient } from "../client/githubClient";

export const treeService = {
  async getRepoTree(owner: string, repo: string, branch: string, token: string) {
    const octokit = createGitHubClient(token);

    const branchInfo = await octokit.request(
      "GET /repos/{owner}/{repo}/branches/{branch}",
      {
        owner,
        repo,
        branch,
      }
    );
    const treeSha = branchInfo.data.commit.commit.tree.sha;
    const tree = await octokit.request(
      "GET /repos/{owner}/{repo}/git/trees/{tree_sha}",
      {
        owner,
        repo,
        tree_sha: treeSha,
        recursive: "1",
      }
    );

    return tree.data;
  }
};
