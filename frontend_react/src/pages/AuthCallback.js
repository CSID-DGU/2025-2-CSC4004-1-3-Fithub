// src/pages/AuthCallback.js
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    async function processLogin() {
      try {
        // 백엔드에서 token + user 받아오기
        const res = await fetch("/auth/github/callback", {
          credentials: "include",
        });

        const data = await res.json();
        console.log("OAuth callback response:", data);

        if (!data.token || !data.user) {
          alert("로그인 실패");
          navigate("/login");
          return;
        }

        login(data.user, data.token);
        navigate("/");

      } catch (err) {
        console.error("OAuth 처리 중 오류:", err);
        alert("로그인 처리 중 오류 발생");
        navigate("/login");
      }
    }

    processLogin();
  }, []);

  return <div style={{ padding: 40 }}>로그인 처리 중...</div>;
}
