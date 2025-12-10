import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getCommits, getCommitDetail } from "../../api/githubApi";

export default function Commit() {
  const { token } = useAuth();
  const repoId = localStorage.getItem("selectedRepo");

  const [commits, setCommits] = useState([]);
  const [openCommitSha, setOpenCommitSha] = useState(null);
  const [commitDetail, setCommitDetail] = useState({}); // 캐싱용
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (!repoId || !token) return;
    loadCommits();
  }, [repoId, token]);

  const loadCommits = async () => {
    try {
      const list = await getCommits(repoId, token);
      setCommits(list);
    } catch (err) {
      console.error(err);
    }
  };

  async function toggleDetail(sha) {
    if (openCommitSha === sha) {
      setOpenCommitSha(null); // 이미 열려있으면 닫기
      return;
    }
    
    setOpenCommitSha(sha);
    
    // 이미 불러온 데이터가 없으면 API 호출
    if (!commitDetail[sha]) {
      setLoadingDetail(true);
      try {
        const detail = await getCommitDetail(repoId, sha, token);
        setCommitDetail((prev) => ({ ...prev, [sha]: detail }));
      } catch (err) {
        console.error(err);
      }
      setLoadingDetail(false);
    }
  }

  return (
    <div className="dashboard-container">
      <div style={{ marginBottom: "25px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "700", color: "#333" }}>📜 Commit History</h2>
        <p style={{ color: "#666", fontSize: "14px", marginTop: "4px" }}>
          프로젝트의 상세 변경 이력을 타임라인으로 확인합니다.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {commits.map((c) => {
          const isOpen = openCommitSha === c.commit_sha;

          return (
            <div 
              key={c.commit_sha} 
              style={{ 
                background: "white", 
                borderRadius: "10px", 
                border: "1px solid #e0e0e0",
                overflow: "hidden",
                boxShadow: isOpen ? "0 4px 12px rgba(0,0,0,0.08)" : "none",
                transition: "all 0.2s ease"
              }}
            >
              {/* 1. 커밋 헤더 (항상 보임) */}
              <div
                onClick={() => toggleDetail(c.commit_sha)}
                style={{
                  padding: "18px 20px",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  background: isOpen ? "#f8f9fa" : "white",
                  borderLeft: isOpen ? "4px solid #4a90e2" : "4px solid transparent"
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    fontWeight: "600", 
                    fontSize: "16px", 
                    color: "#333", 
                    marginBottom: "6px" 
                  }}>
                    {c.message}
                  </div>
                  <div style={{ fontSize: "13px", color: "#888", display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontWeight: "500", color: "#555" }}>{c.author_name}</span>
                    <span>•</span>
                    <span>{new Date(c.date).toLocaleString()}</span>
                  </div>
                </div>
                
                {/* 화살표 아이콘 */}
                <div style={{ color: "#aaa", transform: isOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "0.2s" }}>
                  ▼
                </div>
              </div>

              {/* 2. 상세 내용 (클릭 시 열림) */}
              {isOpen && (
                <div style={{ 
                  borderTop: "1px solid #eee", 
                  padding: "20px 24px",
                  background: "#fff" 
                }}>
                  {loadingDetail ? (
                    <p style={{ color: "#666", fontSize: "14px" }}>상세 정보를 불러오는 중입니다...</p>
                  ) : (
                    <>
                      {/* 상세 정보 요약 */}
                      <div style={{ display: "flex", gap: "20px", marginBottom: "20px", fontSize: "14px", color: "#555" }}>
                        <div>
                          <span style={{ fontWeight: "600", color: "#333" }}>Commit SHA:</span> 
                          <span style={{ marginLeft: "6px", fontFamily: "monospace", background: "#eee", padding: "2px 6px", borderRadius: "4px" }}>
                            {c.commit_sha.substring(0, 7)}
                          </span>
                        </div>
                        <div>
                          <span style={{ fontWeight: "600", color: "#333" }}>Email:</span> 
                          <span style={{ marginLeft: "6px" }}>{commitDetail[c.commit_sha]?.author_email}</span>
                        </div>
                      </div>

                      {/* 변경된 파일 리스트 */}
                      <h4 style={{ fontSize: "15px", fontWeight: "700", marginBottom: "12px", color: "#333" }}>
                        📂 Changed Files
                      </h4>
                      
                      {!commitDetail[c.commit_sha]?.files?.length ? (
                        <p style={{ color: "#999", fontSize: "14px" }}>변경 내역이 없습니다.</p>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                          {commitDetail[c.commit_sha].files.map((f, idx) => (
                            <div 
                              key={idx} 
                              style={{ 
                                display: "flex", 
                                alignItems: "center", 
                                fontSize: "14px",
                                background: "#f9f9f9",
                                padding: "8px 12px",
                                borderRadius: "6px",
                                border: "1px solid #eee"
                              }}
                            >
                              <span style={{ color: "#555", fontFamily: "monospace", flex: 1 }}>
                                {f.filename}
                              </span>
                              
                              {/* 변경사항 수치 (API가 제공한다면 표시) */}
                              {(f.changes || f.additions) && (
                                <span style={{ fontSize: "12px", color: "#666" }}>
                                  {f.changes ? `${f.changes} changes` : `+${f.additions} / -${f.deletions}`}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}