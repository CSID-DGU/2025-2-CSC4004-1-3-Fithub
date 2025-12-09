import { createGitHubClient } from "../client/githubClient";

export const issueService = {
  async getIssues(owner: string, repo: string, token: string): Promise<any[]> {
    const octokit = createGitHubClient(token);

    const res = await octokit.request("GET /repos/{owner}/{repo}/issues", {
      owner,
      repo,
      per_page: 100,
      state: "all",
    });

    return res.data.filter((item: any) => !item.pull_request);//pr필터링: issue, pr 같이 조회되는 문제 해결
  },
};
