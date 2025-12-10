// src/api/githubApi.js

// Repo 기본 정보 조회
export async function getRepoInfo(repoId, token) {
  const res = await fetch(`/github/repos/${repoId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("Repo 정보 조회 실패");
  return res.json();
}

// Repo 파일 트리 (실시간 GitHub API)
export async function getLiveFileTree(repoId, token) {
  const res = await fetch(`/github/repos/files/tree`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ repoId })
  });
  if (!res.ok) throw new Error("파일 트리 조회 실패");
  return res.json();
}

// Repo 파일 목록 (DB)
export async function getFiles(repoId, token) {
  const res = await fetch(`/github/repos/${repoId}/files`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("파일 목록 조회 실패");
  return res.json();
}

// 파일 상세 조회
export async function getFileDetail(repoId, fileId, token) {
  const res = await fetch(`/github/repos/${repoId}/files/${fileId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("파일 상세 조회 실패");
  return res.json();
}

// Commit 리스트
export async function getCommits(repoId, token) {
  const res = await fetch(`/github/repos/${repoId}/commits`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("커밋 리스트 조회 실패");
  return res.json();
}

// Commit 상세
export async function getCommitDetail(repoId, sha, token) {
  const res = await fetch(`/github/repos/${repoId}/commits/${sha}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("커밋 상세 조회 실패");
  return res.json();
}

// Issue 리스트
export async function getIssues(repoId, token) {
  const res = await fetch(`/github/repos/${repoId}/issues`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("이슈 조회 실패");
  return res.json();
}

// Issue 상세 조회
export async function getIssueDetail(repoId, issueId, token) {
  const res = await fetch(`/github/repos/${repoId}/issues/${issueId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("이슈 상세 조회 실패");
  return res.json();
}

// Pull Request 리스트
export async function getPulls(repoId, token) {
  const res = await fetch(`/github/repos/${repoId}/pulls`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("PR 조회 실패");
  return res.json();
}

// Pull Request 상세
export async function getPullDetail(repoId, pullId, token) {
  const res = await fetch(`/github/repos/${repoId}/pulls/${pullId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("PR 상세 조회 실패");
  return res.json();
}
