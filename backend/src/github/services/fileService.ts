import { createGitHubClient } from "../client/githubClient";

export const fileService = {
  async getFileContent(owner: string, repo: string, path: string, token: string) {
    const octokit = createGitHubClient(token);

    const res = await octokit.request(
      "GET /repos/{owner}/{repo}/contents/{path}",
      {
        owner,
        repo,
        path,
      }
    );

    //base64 -> utf-8 decoding
    if (res.data && "content" in res.data && typeof res.data.content === "string") {
      return Buffer.from(res.data.content, "base64").toString("utf8");
    }
    return null;
  },
};

