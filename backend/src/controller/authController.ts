//github authorization
import { Request, Response } from "express";
import * as authService from "../github/services/authService";

//github login
export const githubOAuthLogin = async (req: Request, res: Response) => {
  try {
    const { code } = req.body;

    if (!code) {
        return res.status(400).json({ error: "Missing 'code' in request body" });
    }

    const result = await authService.loginWithGitHub(code);

    res.json({
      token: result.token,
      user: result.user,
    });
  } catch (err: any) {
    console.error("GitHub OAuth error:", err);
    res.status(500).json({
      error: "Failed to login with GitHub",
      detail: err?.message,
    });
  }
};


//callback -> get jwt 
export const githubOAuthCallback = async (req: Request, res: Response) => {
  try {
    const { code } = req.query;

    if (!code) {
      return res.status(400).json({ error: "Missing 'code' in query" });
    }

    // code -> GitHub -> access token -> userProfile -> JWT
    const result = await authService.loginWithGitHub(String(code));

    return res.status(200).json({
      token: result.token,
      user: result.user,
    });

  } catch (err: any) {
    console.error("GitHub OAuth Callback Error:", err);
    res.status(500).json({
      error: "GitHub OAuth callback failed",
      detail: err?.message,
    });
  }
};
