import { createGitHubClient } from "../client/githubClient";

export const treeService = {
  async getRepoTree(owner: string, repo: string, branch: string, token: string) {
    const octokit = createGitHubClient(token);

    const res = await octokit.request(
      "GET /repos/{owner}/{repo}/git/trees/{branch}",
      {
        owner,
        repo,
        branch,
        recursive: "1",
      }
    );
    return res.data;
  },
};
