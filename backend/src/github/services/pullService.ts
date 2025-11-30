import { createGitHubClient } from "../client/githubClient";

export const pullService = {
  async getPullRequests(owner: string, repo: string, token: string) {
    const octokit = createGitHubClient(token);

    const res = await octokit.request(
      "GET /repos/{owner}/{repo}/pulls",
      {
        owner,
        repo,
        per_page: 100,
        state: "all",
      }
    );

    return res.data;
  },
};
