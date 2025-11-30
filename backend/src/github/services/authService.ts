import prisma from "../../prisma";
import { signToken } from "../../jwt";
import fetch from "node-fetch";

const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID!;
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET!;
const GITHUB_REDIRECT_URI = process.env.GITHUB_REDIRECT_URI!;

interface GitHubAccessTokenResponse {
  access_token: string;
  token_type: string;
  scope: string;
}

interface GitHubUserResponse {
  id: number;
  login: string;
  avatar_url?: string;
  name?: string;
  email?: string;
}

export const loginWithGitHub = async (code: string) => {
  if (!code) {
    throw new Error("Missing GitHub OAuth code");
  }

  //code -> access token 
  const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      client_id: GITHUB_CLIENT_ID,
      client_secret: GITHUB_CLIENT_SECRET,
      code,
      redirect_uri: GITHUB_REDIRECT_URI,
    }),
  });

  if (!tokenRes.ok) {
    throw new Error("Failed to fetch GitHub access token");
  }

  const tokenData = (await tokenRes.json()) as GitHubAccessTokenResponse & {
    error?: string;
    error_description?: string;
  };

  if (!tokenData.access_token) {
    throw new Error(
      `GitHub OAuth error: ${tokenData.error || "no access_token"}`
    );
  }

  const accessToken = tokenData.access_token;

  //access token -> get user info
  const userRes = await fetch("https://api.github.com/user", {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!userRes.ok) {
    throw new Error("Failed to fetch GitHub user profile");
  }

  const ghUser = (await userRes.json()) as GitHubUserResponse;

  //user upsert
  const user = await prisma.user.upsert({
    where: { githubId: String(ghUser.id) },
    update: {
      login: ghUser.login,
      avatarUrl: ghUser.avatar_url,
      name: ghUser.name,
      email: ghUser.email,
    },
    create: {
      githubId: String(ghUser.id),
      login: ghUser.login,
      avatarUrl: ghUser.avatar_url,
      name: ghUser.name,
      email: ghUser.email,
    },
  });

  //get JWT
  const token = signToken({ userId: user.id });

  return {
    token,
    user,
  };
};
