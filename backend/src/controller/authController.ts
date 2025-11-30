//github authorization
import { Request, Response } from "express";
import * as authService from "../github/services/authService";

//github login (front → backend)
export const githubOAuthLogin = async (req: Request, res: Response) => {
  try {
    const { code } = req.body;

    if (!code) {
        return res.status(400).json({ error: "Missing 'code' in request body" });
    }

    const result = await authService.loginWithGitHub(code);

    return res.json({
      token: result.token,
      user: result.user,
    });
  } catch (err: any) {
    console.error("GitHub OAuth error:", err);
    return res.status(500).json({
      error: "Failed to login with GitHub",
      detail: err?.message,
    });
  }
};


//callback -> GitHub OAuth redirect after login (GitHub → backend)
export const githubOAuthCallback = async (req: Request, res: Response) => {
  try {
    const { code } = req.query;

    if (!code) {
      return res.status(400).json({ error: "Missing 'code' in query" });
    }

    // GitHub OAuth → access_token → user → JWT
    const result = await authService.loginWithGitHub(String(code));

    const jwt = result.token;

    return res.redirect(`http://localhost:3000/oauth/success?token=${jwt}`);

  } catch (err: any) {
    console.error("GitHub OAuth Callback Error:", err);
    return res.status(500).json({
      error: "GitHub OAuth callback failed",
      detail: err?.message,
    });
  }
};
