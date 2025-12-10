import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Header from "./components/Header";
import Login from "./pages/Login";
import MyPage from "./pages/etc/MyPage";

import CodeGraphPage from "./pages/code/CodeGraphPage";
import CodeOwners from "./pages/code/CodeOwnersPage";
import CodeSummary from "./pages/code/CodeSummaryPage";
import TaskOverview from "./pages/task/TaskOverview";
import TaskList from "./pages/task/TaskList";

import ProjectCreate from "./pages/ProjectCreate";
import MainDashboard from "./pages/MainDashboard";
import Issue from "./pages/etc/Issue";
import Commit from "./pages/etc/Commit";
import PullRequest from "./pages/PullRequest";
import AuthSuccess from "./pages/AuthSuccess";
import ProjectDetail from "./pages/ProjectDetail";

import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import "./styles/Global.css";
import "./styles/Dashboard.css";
import "./styles/Auth.css";
import "./styles/MyPage.css";

import GraphTest from "./pages/GraphTest"; // 테스트용

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Header />

        <Routes>
          {/* 테스트용 */}
          <Route path="/test" element={<GraphTest />} />

          {/* GitHub OAuth */}
          <Route path="/oauth/success" element={<AuthSuccess />} />

          {/* 로그인 */}
          <Route path="/login" element={<Login />} />

          {/* 메인 대시보드 */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <MainDashboard />
              </ProtectedRoute>
            }
          />

          {/* 프로젝트 생성 */}
          <Route
            path="/projects/create"
            element={
              <ProtectedRoute>
                <ProjectCreate />
              </ProtectedRoute>
            }
          />

          {/* 프로젝트 상세 */}
          <Route
            path="/projects/:projectId"
            element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            }
          />

          {/* CODE */}
          <Route
            path="/code/graph/:repoId?"
            element={
              <ProtectedRoute>
                <CodeGraphPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/code/summary"
            element={
              <ProtectedRoute>
                <CodeSummary />
              </ProtectedRoute>
            }
          />

          <Route
            path="/code/owners"
            element={
              <ProtectedRoute>
                <CodeOwners />
              </ProtectedRoute>
            }
          />

          {/* TASK */}
          <Route
            path="/task/overview"
            element={
              <ProtectedRoute>
                <TaskOverview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/task/list"
            element={
              <ProtectedRoute>
                <TaskList />
              </ProtectedRoute>
            }
          />

          {/* 기타 */}
          <Route
            path="/issue"
            element={
              <ProtectedRoute>
                <Issue />
              </ProtectedRoute>
            }
          />

          <Route
            path="/commit"
            element={
              <ProtectedRoute>
                <Commit />
              </ProtectedRoute>
            }
          />

          <Route 
            path="/pulls" 
            element={
              <ProtectedRoute>
                <PullRequest />
              </ProtectedRoute>
            } 
          />

          <Route
            path="/mypage"
            element={
              <ProtectedRoute>
                <MyPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
