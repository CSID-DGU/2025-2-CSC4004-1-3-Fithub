//setupProxy.js

const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    [
      "/auth",
      "/projects",
      "/github",
      "/summaries",
      "/tasks",
      "/api",
      "/graph",
      "/users",
      "/analysis",
    ],
    createProxyMiddleware({
      target: "https://toniest-personable-patty.ngrok-free.dev",
      changeOrigin: true,
      secure: false,   // ngrok SSL 문제 방지
    })
  );
};
