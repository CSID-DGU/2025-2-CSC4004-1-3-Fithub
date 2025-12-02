// src/github/services/authService.ts

import axios from "axios";
import prisma from "../../prisma";
import jwt from "jsonwebtoken";

export const loginWithGitHub = async (code: string) => {
  //request for Access Token
  const tokenResponse = await axios.post(
    "https://github.com/login/oauth/access_token",
    {
      client_id: process.env.GITHUB_CLIENT_ID,
      client_secret: process.env.GITHUB_CLIENT_SECRET,
      code,
    },
    {
      headers: { Accept: "application/json" },
    }
  );

  const accessToken = tokenResponse.data.access_token;
  if (!accessToken) throw new Error("GitHub access token not received");

  //request Github User Data
  const userResponse = await axios.get("https://api.github.com/user", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  const gh = userResponse.data;

  let user = await prisma.user.findUnique({
    where: { githubId: gh.id.toString() },
  });

  if (!user) {
    user = await prisma.user.create({
      data: {
        githubId: gh.id.toString(),
        login: gh.login,
        avatarUrl: gh.avatar_url,
        name: gh.name,
        email: gh.email,
      },
    });
  }

  //store Github Access Token to database
  await prisma.user.update({
    where: { id: user.id },
    data: { githubAccessToken: accessToken },
  });

  //get JWT
  const token = jwt.sign(
    { userId: user.id },     
    process.env.JWT_SECRET!,
    { expiresIn: "7d" }
  );

  return { token, user };
};
