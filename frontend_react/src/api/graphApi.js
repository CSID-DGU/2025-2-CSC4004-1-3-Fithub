// src/api/graphApi.js

// Repo 기반 그래프 생성
export async function generateGraph(repoId) {
  const res = await fetch(`/graph/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repoId })
  });

  if (!res.ok) throw new Error("그래프 생성 실패");
  return res.json();
}

// Repo 그래프 데이터 조회
export async function getGraphData(repoId) {
  const res = await fetch(`/graph/${repoId}`);
  if (!res.ok) throw new Error("그래프 데이터 조회 실패");
  return res.json();
}
