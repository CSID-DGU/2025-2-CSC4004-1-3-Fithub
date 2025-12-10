const BASE = "/projects";

// 1) 프로젝트 생성 (DB 저장)
export async function createProject({ name, description }, token) {
  const res = await fetch(`${BASE}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ name, description })
  });

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 2) 프로젝트 목록 조회  (DB) GET /projects/lists
export async function getProjectList(token) {
  const res = await fetch(`/projects/lists`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!res.ok) throw new Error("프로젝트 목록 조회 실패");
  return res.json();
}

// 3) 프로젝트 상세 조회 (DB)
export async function getProject(projectId, token) {
  const res = await fetch(`${BASE}/${projectId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!res.ok) throw new Error("프로젝트 조회 실패");
  return res.json();
}

// 4) Repo 연결
export async function addRepoToProject(projectId, owner, repo, token) {
  const res = await fetch(`${BASE}/${projectId}/repos`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ owner, repo })
  });

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 5) 프로젝트 삭제
export async function deleteProject(projectId, token) {
  const res = await fetch(`${BASE}/${projectId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!res.ok) throw new Error(await res.text());
  return true;
}

// 6) Snapshot 실행
export async function startSnapshot(repoFullName, token) {
  const res = await fetch(`/github/repo-snapshot`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ repoFullName })
  });

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 7) Member 추가
export async function addProjectMember(projectId, userId, token) {
  const res = await fetch(`/projects/${projectId}/members`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ userId })
  });

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
