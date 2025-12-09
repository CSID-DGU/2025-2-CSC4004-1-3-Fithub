import { createGitHubClient } from "../client/githubClient";

export const commitService = {
  
  //get commit lists
  async getCommits(owner: string, repo: string, token: string) {
    const octokit = createGitHubClient(token);

    const res = await octokit.request("GET /repos/{owner}/{repo}/commits", {
      owner,
      repo,
      per_page: 100,
    });

    return res.data;
  },

  //get commit details
  async getCommitDetail(owner: string, repo: string, sha: string, token: string) {
    const octokit = createGitHubClient(token);

    const res = await octokit.request("GET /repos/{owner}/{repo}/commits/{sha}", {
      owner,
      repo,
      sha
    });

    return res.data;
  },
};

