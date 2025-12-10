import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getProjectTasks, generateTasks } from "../../api/taskApi";
import "../../styles/Task.css";

export default function TaskOverview() {
  const { token } = useAuth();
  const projectId = localStorage.getItem("currentProjectId");

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);

  useEffect(() => {
    if (token && projectId) loadTasks();
  }, [token, projectId]);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await getProjectTasks(projectId, token);
      setTasks(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleGenerateAI = async () => {
    if (!window.confirm("AI가 코드를 분석하여 프로젝트 Task를 생성합니다. 진행할까요?")) return;
    
    setGenLoading(true);
    try {
      await generateTasks(projectId, token);
      alert("AI가 작업을 생성했습니다!");
      loadTasks(); // 목록 갱신
    } catch (err) {
      alert("생성 실패: " + err.message);
    }
    setGenLoading(false);
  };

  // 간단한 통계 계산
  const total = tasks.length;
  const todo = tasks.filter(t => t.status === "TODO").length;
  const inProgress = tasks.filter(t => t.status === "IN_PROGRESS").length;
  const done = tasks.filter(t => t.status === "DONE").length;

  return (
    <div className="task-container">
      <div className="task-header">
        <h2>📊 Task Overview</h2>
        <button 
          className="ai-btn" 
          onClick={handleGenerateAI} 
          disabled={genLoading}
        >
          {genLoading ? "AI 생성 중..." : "✨ AI Task Auto-Generate"}
        </button>
      </div>

      {/* 대시보드 요약 카드 */}
      <div className="status-board">
        <div className="status-card total">
          <h3>Total</h3>
          <p>{total}</p>
        </div>
        <div className="status-card todo">
          <h3>To Do</h3>
          <p>{todo}</p>
        </div>
        <div className="status-card progress">
          <h3>In Progress</h3>
          <p>{inProgress}</p>
        </div>
        <div className="status-card done">
          <h3>Done</h3>
          <p>{done}</p>
        </div>
      </div>

      {/* 전체 작업 리스트 */}
      <div className="task-list-section">
        <h3>All Project Tasks</h3>
        {loading ? <p>로딩 중...</p> : (
          <table className="task-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Assignee</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td><span className={`badge ${task.status}`}>{task.status}</span></td>
                  <td>{task.title}</td>
                  <td>{task.priority || "Medium"}</td>
                  <td>{task.assignee || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}