// src/pages/Login.js
import React from "react";

function Login() {
  const handleGithubLogin = () => {
    window.location.href = "/auth/github/login";
  };

  return (
    <div className="main-dashboard">
      <main className="dashboard-main">
        <div className="login-box">
          <h2 style={{ textAlign: "center", marginBottom: 20 }}>Sign In</h2>
          <button className="btn-primary" onClick={handleGithubLogin}>
            Sign in with GitHub
          </button>
        </div>
      </main>
    </div>
  );
}

export default Login;
