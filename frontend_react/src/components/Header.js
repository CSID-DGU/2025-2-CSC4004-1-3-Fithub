import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../styles/Header.css";

function Header() {
  const navigate = useNavigate();
  const [openMenu, setOpenMenu] = useState(null);

  // AuthContext에서 로그인 정보 가져옴
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    localStorage.removeItem("selectedRepo");
    navigate("/");
  };

  // 공통: 레포 체크
  const checkRepo = () => {
    const repo = localStorage.getItem("selectedRepo");
    if (!repo) {
      alert("먼저 Repository를 선택해주세요.");
      return false;
    }
    return true;
  };

  // 메뉴 이동
  const goMenu = (path) => {
    if (!user) {
      alert("로그인 후 이용해주세요.");
      return navigate("/login");
    }
    if (!checkRepo()) return;
    navigate(path);
  };

  // 상단 링크
  const goOrLogin = (path) => {
    if (!user) {
      alert("로그인 후 이용해주세요.");
      return navigate("/login");
    }
    if (!checkRepo()) return;
    navigate(path);
  };

  return (
    <header className="header">
      <div className="logo" onClick={() => navigate("/")}>FITHUB</div>

      <nav className="nav">
        {/* ---------------- CODE ---------------- */}
        <div
          className="nav-item"
          onClick={() =>
            setOpenMenu(openMenu === "code" ? null : "code")
          }
        >
          Code ▾
          {openMenu === "code" && (
            <div className="dropdown">
              <span onClick={() => goMenu("/code/graph")}>Code Graph</span>
              <span onClick={() => goMenu("/code/summary")}>Summary</span>
              <span onClick={() => goMenu("/code/owners")}>Owners</span>
            </div>
          )}
        </div>

        {/* ---------------- TASK ---------------- */}
        <div
          className="nav-item"
          onClick={() =>
            setOpenMenu(openMenu === "task" ? null : "task")
          }
        >
          Task ▾
          {openMenu === "task" && (
            <div className="dropdown">
              <span onClick={() => goMenu("/task/overview")}>Task Overview</span>
              <span onClick={() => goMenu("/task/list")}>Task List</span>
            </div>
          )}
        </div>

        <span className="nav-item" onClick={() => goOrLogin("/issue")}>Issue</span>
        <span className="nav-item" onClick={() => goOrLogin("/pulls")}>PR</span>
        <span className="nav-item" onClick={() => goOrLogin("/commit")}>Commit</span>
        <span className="nav-item" onClick={() => navigate("/mypage")}>
          My Page
        </span>
      </nav>

      {user ? (
        <button className="signout-btn" onClick={handleLogout}>
          Sign Out
        </button>
      ) : (
        <button className="signout-btn" onClick={() => navigate("/login")}>
          Login
        </button>
      )}
    </header>
  );
}

export default Header;
