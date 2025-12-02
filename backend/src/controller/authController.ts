import { Request, Response } from "express";
import * as authService from "../github/services/authService";

//GitHub OAuth login front -> backend): return token + user 
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

//GitHub OAuth callback (GitHub -> backend -> redirect to front)
export const githubOAuthCallback = async (req: Request, res: Response) => {
  try {
    const { code } = req.query;

    if (!code) {
      return res.status(400).json({ error: "Missing 'code' in query" });
    }

    const result = await authService.loginWithGitHub(String(code));

    const FRONTEND_URL = "http://localhost:3000/oauth/success";

    return res.redirect(`${FRONTEND_URL}?token=${result.token}`);

  } catch (err: any) {
    console.error("GitHub OAuth Callback Error:", err);
    return res.status(500).json({
      error: "GitHub OAuth callback failed",
      detail: err?.message,
    });
  }
};
