import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getMyRoleTasks } from "../../api/taskApi";
import "../../styles/Task.css";

export default function TaskList() {
  const { token, user } = useAuth();
  const [myTasks, setMyTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) loadMyTasks();
  }, [token]);

  const loadMyTasks = async () => {
    try {
      const data = await getMyRoleTasks(token);
      setMyTasks(data);
    } catch (err) {
      console.error(err);
      // alert("내 작업을 불러오지 못했습니다.");
    }
    setLoading(false);
  };

  return (
    <div className="task-container">
      <h2>📋 My Tasks (Role Based)</h2>
      <p style={{ color: "#666", marginBottom: "20px" }}>
        {user?.login}님의 역할에 맞춰 배정된 작업 목록입니다.
      </p>

      {loading ? (
        <p>내 작업 불러오는 중...</p>
      ) : myTasks.length === 0 ? (
        <div className="empty-state">
          <p>현재 할당된 작업이 없거나, 역할(Role)이 설정되지 않았습니다.</p>
          <p>프로젝트 관리 페이지에서 역할을 설정해주세요.</p>
        </div>
      ) : (
        <div className="my-task-grid">
          {myTasks.map((task) => (
            <div key={task.id} className="task-card-item">
              <div className="task-card-header">
                <span className={`badge ${task.status}`}>{task.status}</span>
                <span className="priority">{task.priority}</span>
              </div>
              <h4>{task.title}</h4>
              <p>{task.description || "상세 설명이 없습니다."}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}