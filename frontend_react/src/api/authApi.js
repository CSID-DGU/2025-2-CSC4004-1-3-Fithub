// src/api/authApi.js
// 깃허브 로그인 (브라우저 이동)
export function githubLogin() {
  window.location.href = "/auth/github/login";
}

// 백엔드에서 JWT + 사용자 정보 가져오기
export async function getMyInfo(token) {
  const res = await fetch("/users/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "ngrok-skip-browser-warning": "69420",
    },
  });

  if (!res.ok) throw new Error("유저 정보 조회 실패");

  return res.json(); // { user }
}
