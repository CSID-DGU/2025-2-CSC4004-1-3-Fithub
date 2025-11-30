import { createGitHubClient } from "../client/githubClient";

export const repoService = {
  async getRepoInfo(owner: string, repo: string, token: string) {
    const octokit = createGitHubClient(token);

    const res = await octokit.request(
      "GET /repos/{owner}/{repo}",
      {
        owner,
        repo,
      }
    );

    return res.data;
  },
};
