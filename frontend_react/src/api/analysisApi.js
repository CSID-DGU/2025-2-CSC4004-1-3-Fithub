// src/api/analysisApi.js

// 1. 분석 시작 요청 (runId 반환)
export async function startAnalysis(repoId, repoName, projectId) {
  const response = await fetch("/analysis/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "69420",
    },
    body: JSON.stringify({
      repo: {
        repo_id: repoId.toString(),
        name: repoName,
        local_path: null
      },
      options: {},
      thresholds: { consistency_min: 0.7, retry_max: 2 },
      projectId: projectId // 팀원 자료에 projectId가 추가됨
    }),
  });

  if (!response.ok) throw new Error(`분석 요청 실패: ${response.status}`);
  return response.json(); // { runId: "..." }
}

// 2. 진행 상태 확인 ("processing" or "completed")
export async function checkAnalysisStatus(runId) {
  const response = await fetch(`/analysis/status/${runId}`, {
    headers: { "ngrok-skip-browser-warning": "69420" },
  });
  if (!response.ok) throw new Error(`상태 조회 실패: ${response.status}`);
  return response.json(); // { status: "processing" | "completed" }
}

// 3. 그래프 데이터 조회 (Structural JSON)
export async function getAnalysisGraph(runId) {
  const response = await fetch(`/analysis/result/${runId}`, {
    headers: { "ngrok-skip-browser-warning": "69420" },
  });
  if (!response.ok) throw new Error(`그래프 조회 실패: ${response.status}`);
  return response.json(); 
}

// 4. 요약 데이터 조회 (DB 파싱 결과)
export async function getAnalysisSummary(runId) {
  const response = await fetch(`/summary/${runId}`, {
    headers: { "ngrok-skip-browser-warning": "69420" },
  });
  if (!response.ok) throw new Error(`요약 조회 실패: ${response.status}`);
  return response.json(); 
}

// 5. 태스크(이슈) 조회
export async function getAnalysisTasks(runId) {
  const response = await fetch(`/tasks/${runId}`, {
    headers: { "ngrok-skip-browser-warning": "69420" },
  });
  if (!response.ok) throw new Error(`태스크 조회 실패: ${response.status}`);
  return response.json(); 
}