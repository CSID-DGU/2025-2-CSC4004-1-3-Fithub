import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import { getProject } from "../api/projectApi";
import { getIssues } from "../api/githubApi"; 
import { 
  startAnalysis, 
  checkAnalysisStatus, 
  getAnalysisGraph, 
  getAnalysisSummary, 
  getAnalysisTasks 
} from "../api/analysisApi"; 

import CodeGraph from "../components/CodeGraph";

export default function ProjectDetail() {
  const { projectId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();

  // --- 상태 관리 ---
  const [project, setProject] = useState(null);
  const [repo, setRepo] = useState(null);
  
  const [summaryList, setSummaryList] = useState([]); 
  const [repoSummary, setRepoSummary] = useState(""); 
  const [issues, setIssues] = useState([]); 
  const [graph, setGraph] = useState(null);
  
  const [pageLoading, setPageLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false); // 분석 중인지 여부
  const [statusMessage, setStatusMessage] = useState("");
  
  // 현재 실행 중인 RunID
  const [currentRunId, setCurrentRunId] = useState(null);

  // 초기 로드
  useEffect(() => {
    async function loadInitialData() {
      if (!token) {
        alert("로그인이 필요합니다.");
        setPageLoading(false);
        return;
      }
      try {
        const projectData = await getProject(projectId, token);
        setProject(projectData);
        localStorage.setItem("currentProjectId", projectData.id);

        const repoInfo = projectData.repos?.[0];
        setRepo(repoInfo);

        if (repoInfo) {
          localStorage.setItem("selectedRepo", repoInfo.repo_id);
          try {
            const issueList = await getIssues(repoInfo.repo_id, token);
            setIssues(issueList);
          } catch (e) { console.warn("이슈 로딩 실패:", e); }
        }
      } catch (err) {
        console.error("프로젝트 로딩 실패:", err);
      }
      setPageLoading(false);
    }
    loadInitialData();
  }, [projectId, token]);


  // 캐시 확인
  useEffect(() => {
    if (!pageLoading && repo && !graph && !analyzing) {
        const cachedKey = `analysis_cache_${repo.repo_id}`;
        const cachedData = sessionStorage.getItem(cachedKey);
        if (cachedData) {
            console.log("📦 [Cache] 저장된 분석 데이터를 불러옵니다.");
            const parsed = JSON.parse(cachedData);
            
            if (parsed.graph) {
                if (parsed.graph.nodes && parsed.graph.nodes.length > 0) setGraph(parsed.graph);
                else if (parsed.graph.graph && parsed.graph.graph.nodes) setGraph(parsed.graph.graph);
            }
            if (parsed.summary) handleSummaryData(parsed.summary);
            if (parsed.tasks && Array.isArray(parsed.tasks)) setIssues(parsed.tasks);
        } 
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageLoading, repo]); 


  const handleSummaryData = (data) => {
      let list = [];
      if (Array.isArray(data)) list = data;
      else if (data.data) list = data.data;
      else if (data.summary && Array.isArray(data.summary)) list = data.summary;
      setSummaryList(list);
  };


  // [메인 함수] 분석 시작
  const handleRunAnalysis = async () => {
    if (!repo || analyzing) return;
    
    // 🔥 [수정됨] 레포지토리 이름 추출 로직 강화
    // 1. repo_name 또는 name이 있으면 그거 사용
    let targetName = repo.repo_name || repo.name;

    // 2. 이름이 없고 html_url이 있다면? URL에서 이름만 잘라내기
    // 예: "https://github.com/naamy/Fithub" -> "/"로 자름 -> 맨 뒤 "Fithub" 가져옴
    if (!targetName && repo.html_url) {
        try {
            const parts = repo.html_url.split('/');
            // 맨 뒤가 비어있을 수도 있으니(trailing slash) 필터링
            const validParts = parts.filter(p => p.trim() !== "");
            targetName = validParts[validParts.length - 1]; 
            console.log(`✂️ URL에서 레포 이름 추출 성공: ${targetName}`);
        } catch (e) {
            console.error("URL 파싱 실패:", e);
        }
    }

    // 3. 그래도 없으면 에러 처리
    if (!targetName) {
        console.error("🚨 레포지토리 이름 없음:", repo);
        alert(
            "레포지토리 이름을 찾을 수 없습니다.\n" +
            "관리자에게 문의하거나 repo 데이터를 확인해주세요.\n\n" +
            "현재 데이터: " + JSON.stringify(repo, null, 2)
        );
        return;
    }
    
    sessionStorage.removeItem(`analysis_cache_${repo.repo_id}`);
    setAnalyzing(true);
    setGraph(null); // 그래프 초기화 (로딩 화면 표시용)
    setCurrentRunId(null); 
    setStatusMessage("분석 요청 중...");
    
    try {
      // 1. 분석 시작 요청만
      console.log(`🚀 분석 시작 요청: ID=${repo.repo_id}, Name=${targetName}`);
      const startRes = await startAnalysis(repo.repo_id, targetName, project.id);
      const runId = startRes.runId; 
      
      setCurrentRunId(runId); 
      console.log(`🚀 분석 시작! RunID: ${runId}`);

      // 2. 자동 확인(While Loop) 삭제됨 -> 수동 확인 유도
      setStatusMessage("분석 시작됨. [상태 확인] 버튼을 눌러주세요.");
      alert("분석이 시작되었습니다.\n진행 상황을 보려면 [🔄 분석 상태 확인] 버튼을 눌러주세요.");

    } catch (err) {
      console.error("🚨 분석 요청 실패:", err);
      alert(`분석 요청 중 오류가 발생했습니다.\n${err.message}`);
      setAnalyzing(false);
      setStatusMessage("");
    }
  };


  // 사용자가 누를 때만 작동하는 상태 확인 함수
  const handleManualStatusCheck = async () => {
    // 1. 분석 중이 아닐 때
    if (!currentRunId) {
        alert("현재 진행 중인 분석 작업이 없습니다.\n먼저 [AI 코드 분석 시작] 버튼을 눌러주세요.");
        return;
    }

    // 2. 상태 확인
    try {
        console.log(`🕵️ [Manual] 상태 확인 요청: RunID=${currentRunId}`);
        const statusRes = await checkAnalysisStatus(currentRunId);
        const status = statusRes.status;
        
        console.log(`📡 [Manual] 상태: ${status}`);
        
        if (status === "processing") {
            // 아직 하는 중 -> Alert만 띄우고 끝
            alert(`[현재 상태: Processing]\nAI가 열심히 분석 중입니다.\n잠시 후 다시 눌러주세요.`);
            setStatusMessage("분석 중... (Processing)");
        
        } else if (status === "partial") {
            // 부분 완료 -> 데이터 가져오기 + 분석 상태 유지 (Analyzing = true)
            alert(`[현재 상태: Partial]\n부분적으로 완료되었습니다!\n현재까지의 그래프를 가져옵니다.`);
            setStatusMessage("분석 중... (Partial - 그래프 갱신됨)");
            await fetchAndSetResults(currentRunId);
            
        } else if (status === "completed") {
            // 완전 완료 -> 데이터 가져오기 + 분석 종료 (Analyzing = false)
            alert(`[현재 상태: Completed]\n분석이 모두 완료되었습니다!`);
            setStatusMessage("분석 완료");
            await fetchAndSetResults(currentRunId);
            
            // 분석 종료 처리
            setAnalyzing(false);
            setCurrentRunId(null);
        
        } else if (status === "failed") {
            // 실패 -> 분석 종료
            alert(`[현재 상태: Failed]\n분석에 실패했습니다.`);
            setAnalyzing(false);
            setCurrentRunId(null);
            setStatusMessage("분석 실패");
        }

    } catch (e) {
        console.error(e);
        alert("상태 확인 실패 (서버 응답 없음)");
    }
  };


  // 결과 데이터 가져오기
  const fetchAndSetResults = async (runId) => {
      const [graphData, summaryData, taskData] = await Promise.all([
        getAnalysisGraph(runId).catch(e => null),
        getAnalysisSummary(runId).catch(e => []),
        getAnalysisTasks(runId).catch(e => [])
      ]);

      // 그래프 데이터 세팅
      if (graphData) {
          let validGraph = null;
          if (graphData.nodes && graphData.nodes.length > 0) validGraph = graphData;
          else if (graphData.graph && graphData.graph.nodes) validGraph = graphData.graph;

          if (validGraph) setGraph(validGraph);
      }

      // 요약 & 태스크 세팅
      if (summaryData) handleSummaryData(summaryData);
      if (taskData && Array.isArray(taskData)) setIssues(taskData);

      // 캐시 저장
      const fullResult = { 
          graph: graphData?.graph || graphData, 
          summary: summaryData, 
          tasks: taskData 
      };
      sessionStorage.setItem(`analysis_cache_${repo.repo_id}`, JSON.stringify(fullResult));
  };


  // 이동 함수
  const handleMoveToGraph = () => {
    if (!repo) return;
    const targetName = repo.repo_name || repo.name || "Unknown Repo";
    if (!graph || ((!graph.nodes || graph.nodes.length === 0) && (!graph.graph || !graph.graph.nodes))) {
        alert("분석된 그래프 데이터가 없습니다.");
        return;
    }
    navigate(`/code/graph/${repo.repo_id}`, { state: { repo: { ...repo, name: targetName }, preloadedData: { graph, summary: summaryList } } });
  };

  const handleMoveToSummary = () => {
    if (!repo) return;
    const targetName = repo.repo_name || repo.name || "Unknown Repo";
    navigate("/code/summary", { state: { repo: { ...repo, name: targetName }, preloadedData: { summary: summaryList, repoSummary: repoSummary } } });
  };


  if (pageLoading) return <div style={{padding: "50px", textAlign: "center"}}>로딩 중...</div>;
  if (!project) return <div style={{padding: "50px", textAlign: "center"}}>프로젝트를 찾을 수 없습니다.</div>;

  const hasGraphData = graph && ((graph.nodes && graph.nodes.length > 0) || (graph.graph && graph.graph.nodes && graph.graph.nodes.length > 0));

  return (
    <div className="dashboard-container" style={{ padding: "20px", maxWidth: "1200px", margin: "0 auto" }}>
      
      <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px"}}>
        <h2 style={{margin: 0}}>{project.name} 대시보드</h2>
        
        <div style={{display: "flex", gap: "10px"}}>
            
            {/* 🔥 [변경] 항상 보이는 상태 확인 버튼 */}
            <button 
                onClick={handleManualStatusCheck} 
                style={{ 
                    padding: "10px 15px", 
                    background: analyzing ? "#28a745" : "#6c757d", // 분석 중이면 초록, 아니면 회색
                    color: "white", 
                    border: "none", 
                    borderRadius: "8px", 
                    cursor: "pointer", 
                    fontWeight: "bold",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.2)"
                }}
            >
                🔄 분석 상태 확인
            </button>

            <button 
                onClick={handleRunAnalysis} 
                disabled={analyzing}
                style={{ padding: "10px 20px", background: analyzing ? "#ccc" : "#007bff", color: "white", border: "none", borderRadius: "8px", cursor: analyzing ? "not-allowed" : "pointer", fontWeight: "bold", display: "flex", alignItems: "center", gap: "8px" }}
            >
                {analyzing ? <>{statusMessage || "⏳ 분석 중..."}</> : <>🔍 AI 코드 분석 시작</>}
            </button>
        </div>
      </div>

      <div className="analysis-grid" style={{ display: "grid", gap: "20px", gridTemplateColumns: "1fr 1fr" }}>

        {/* 1. 코드 요약 카드 */}
        <div className="analysis-card" style={cardStyle}>
          <h3>🧠 코드 요약</h3>
          {repoSummary && (
            <div style={{marginBottom: "15px", padding: "12px", background: "#f8f9fa", borderRadius: "8px", fontSize: "14px", lineHeight: "1.5"}}>
              <strong>📄 전체 요약:</strong> {repoSummary.slice(0, 200)}...
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {summaryList.length === 0 ? (
              <p style={{color: "#888", fontSize: "14px"}}>{analyzing ? "데이터 생성 중..." : "분석된 요약이 없습니다."}</p>
            ) : (
              summaryList.slice(0, 3).map((s, idx) => (
                <div key={idx} style={{fontSize: "14px", borderBottom: "1px solid #eee", paddingBottom: "8px"}}>
                  <span style={{fontWeight: "bold", color: "#333"}}>• {s.file_name || s.path || "파일"}: </span>
                  <span style={{color: "#555"}}>{s.summary ? s.summary.slice(0, 50) : "내용 없음"}...</span>
                </div>
              ))
            )}
          </div>
          <button className="more-btn" onClick={handleMoveToSummary} disabled={summaryList.length === 0} style={{...moreBtnStyle, background: summaryList.length === 0 ? "#ccc" : "#333"}}>전체 보기 →</button>
        </div>

        {/* 2. 이슈 & 태스크 카드 */}
        <div className="analysis-card" style={cardStyle}>
          <h3>🐞 이슈 & 태스크</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {issues.length === 0 ? (
              <p style={{color: "#888", fontSize: "14px"}}>데이터가 없습니다.</p>
            ) : (
              issues.slice(0, 5).map((i, idx) => (
                <div key={i.id || idx} style={{fontSize: "14px", borderBottom: "1px solid #eee", paddingBottom: "8px"}}>
                  <span style={{color: 'green', marginRight: "6px"}}>●</span>
                  {i.title || i.content || "제목 없음"}
                </div>
              ))
            )}
          </div>
          <button className="more-btn" onClick={() => navigate("/issue")} style={moreBtnStyle}>전체 보기 →</button>
        </div>

        {/* 3. 코드 구조 그래프 카드 */}
        <div className="analysis-card" style={{ ...cardStyle, gridColumn: "1 / span 2", minHeight: "500px" }}> 
          <h3>🧩 코드 구조 그래프</h3>
          
          <div style={{ 
              background: hasGraphData ? "#1a1a1a" : "#f8f9fa", 
              height: "400px",       
              display: "flex", 
              flexDirection: "column", 
              alignItems: "center", 
              justifyContent: "center", 
              borderRadius: "12px", 
              overflow: "hidden", 
              position: "relative",
              marginBottom: "15px",
              border: hasGraphData ? "none" : "1px dashed #ccc"
          }}>
            {analyzing && !hasGraphData ? (
              // 1. 분석 중인데 아직 데이터 없음 (Waiting)
              <div style={{textAlign: "center", zIndex: 10}}>
                <div style={{ width: "30px", height: "30px", border: "3px solid #ccc", borderTop: "3px solid #007bff", borderRadius: "50%", animation: "spin 1s linear infinite", margin: "0 auto 10px auto" }} />
                <p style={{color: "#555", fontWeight: "bold", marginTop: "10px"}}>AI가 코드를 분석 중입니다...</p>
                <p style={{color: "#888", fontSize: "12px"}}>상태 확인 버튼을 눌러보세요!</p>
              </div>
            ) : hasGraphData ? (
              // 2. 데이터가 있음 (Partial이든 Completed든)
              <CodeGraph data={{ graph: graph }} />
            ) : (
              // 3. 분석 중도 아니고 데이터도 없음
              <div style={{textAlign: "center"}}>
                <p style={{color: "#888", marginBottom: "5px"}}>분석된 데이터가 없습니다.</p>
                <p style={{color: "#007bff", fontSize: "14px", fontWeight: "bold"}}>
                    ↗ 우측 상단의 [AI 코드 분석 시작] 버튼을 눌러주세요.
                </p>
              </div>
            )}
             <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          </div>

          <button 
            className="more-btn" 
            onClick={handleMoveToGraph} 
            disabled={!hasGraphData} 
            style={{ ...moreBtnStyle, background: (!hasGraphData) ? "#eee" : "#333", cursor: (!hasGraphData) ? "not-allowed" : "pointer" }}
          >
            전체 화면으로 보기 →
          </button>
        </div>

      </div>
    </div>
  );
}

const cardStyle = { background: "white", borderRadius: "12px", padding: "20px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)", display: "flex", flexDirection: "column", justifyContent: "space-between" };
const moreBtnStyle = { marginTop: "15px", padding: "10px", background: "#333", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "bold", width: "100%", textAlign: "center" };