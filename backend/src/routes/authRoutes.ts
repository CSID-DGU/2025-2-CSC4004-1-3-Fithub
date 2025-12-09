import { Router } from "express";
import { githubOAuthLogin, githubOAuthCallback } from "../controller/authController";

const router = Router();

//github login (redirect to github)
router.get("/github/login", (req, res) => {
  const redirectUri = `https://github.com/login/oauth/authorize?client_id=${process.env.GITHUB_CLIENT_ID}&redirect_uri=${process.env.GITHUB_REDIRECT_URI}&scope=repo,read:user,user:email`;
  return res.redirect(redirectUri);
});

//github OAuth callback -> jwt 
router.get("/github/callback", githubOAuthCallback);
router.post("/github", githubOAuthLogin);

export default router;