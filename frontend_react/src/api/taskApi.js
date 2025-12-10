// src/api/taskApi.js

/* -------------------------------
   AI Task 생성 (프로젝트 기반)
-------------------------------- */
export async function generateTasks(projectId, token) {
  const res = await fetch(`/tasks/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    // 백엔드가 projectId를 body로 받는지 확인 필요하지만, 
    // 명세 맥락상 projectId를 보냅니다.
    body: JSON.stringify({ projectId }), 
  });

  if (!res.ok) throw new Error("Task 생성 실패");
  return res.json();
}

/* -------------------------------
   프로젝트 전체 Task 조회
-------------------------------- */
export async function getProjectTasks(projectId, token) {
  const res = await fetch(`/tasks/project/${projectId}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) throw new Error("프로젝트 Task 조회 실패");
  return res.json();
}

/* -------------------------------
   내 역할(Role) 기반 Task 조회
-------------------------------- */
export async function getMyRoleTasks(token) {
  const res = await fetch(`/tasks/my-role`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) throw new Error("내 Task 조회 실패");
  return res.json();
}