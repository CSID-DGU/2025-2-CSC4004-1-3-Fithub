// src/api/summaryApi.js

/* -------------------------------
   프로젝트 요약 조회
-------------------------------- */
export async function getSummary(projectId, token) {
  const res = await fetch(`/summaries/${projectId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("요약 조회 실패");
  return res.json();
}

/* -------------------------------
   프로젝트 요약 저장 (AI가 생성)
-------------------------------- */
export async function saveSummary(projectId, summaryText, token) {
  const res = await fetch(`/summaries`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      projectId,
      text: summaryText
    })
  });

  if (!res.ok) throw new Error("요약 저장 실패");
  return res.json();
}
