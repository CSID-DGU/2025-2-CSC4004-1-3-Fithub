import { Octokit } from "octokit";
const GITHUB_API_VERSION = "2022-11-28";

export function createGitHubClient(token: string) {
  const octokit = new Octokit({
    auth: token,
    request: {
      headers: {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
      },
    },
  });
  return octokit;
}
