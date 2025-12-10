import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getMyInfo } from "../../api/authApi";
import "../styles/MyPage.css";

export default function MyPage() {
  const { token, logout } = useAuth();
  
  // 서버에서 받아온 진짜 유저 정보를 담을 state
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    // 페이지 들어오면 내 정보 가져오기
    async function fetchMe() {
      try {
        const data = await getMyInfo(token);
        console.log("내 정보:", data); // 콘솔에서 데이터 확인용
        setUserInfo(data);
      } catch (err) {
        console.error(err);
        // 에러 나면 조용히 실패하거나, 필요하면 alert
      }
      setLoading(false);
    }

    fetchMe();
  }, [token]);

  if (!token) {
    return <div className="mypage-container-locked"><p>로그인이 필요합니다.</p></div>;
  }

  // 로딩 중일 때 보여줄 화면 (스켈레톤 대신 간단히)
  if (loading) {
    return (
      <div className="mypage-wrapper">
        <p style={{ marginTop: "100px", color: "#666" }}>정보를 불러오는 중...</p>
      </div>
    );
  }

  // 데이터가 없을 경우 (에러 등) 대비용 기본값 설정
  // 백엔드 응답 필드명(예: user_id, avatar_url 등)에 맞춰서 수정이 필요할 수도 있습니다.
  const displayUser = userInfo || {};
  
  // 1. 프로필 이미지
  const profileImage = displayUser.avatarUrl || displayUser.avatar_url || "https://github.com/identicons/jason.png";
  
  // 2. 이름 (nickname -> login -> username 순서로 찾기)
  const displayName = displayUser.nickname || displayUser.login || displayUser.username || "Unknown User";
  
  // 3. GitHub 링크
  const githubUrl = displayUser.html_url || (displayUser.login ? `https://github.com/${displayUser.login}` : null);

  return (
    <div className="mypage-wrapper">
      <div className="profile-card-container">
        
        <div className="profile-cover"></div>

        <div className="profile-content">
          <div className="avatar-wrapper">
            <img 
              src={profileImage} 
              alt="Profile" 
              className="avatar-img"
              onError={(e) => { e.target.src = "https://via.placeholder.com/150?text=No+Img"; }}
            />
          </div>

          <h2 className="profile-name">{displayName}</h2>
          <p className="profile-id">User ID: {displayUser.id || "-"}</p>

          <div className="info-box">
            <div className="info-row">
              <span className="info-label">Email</span>
              <span className="info-value">{displayUser.email || "이메일 정보 없음"}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Role</span>
              <span className="info-value">{displayUser.role || "Developer"}</span> 
            </div>
            <div className="info-row">
              <span className="info-label">GitHub ID</span>
              <span className="info-value">{displayUser.login || "-"}</span> 
            </div>
          </div>

          <div className="action-buttons">
            {githubUrl ? (
              <a 
                href={githubUrl} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="btn-github"
              >
                GitHub 프로필 이동 ↗
              </a>
            ) : (
              <button 
                className="btn-github" 
                style={{ background: "#ccc", cursor: "not-allowed" }}
              >
                GitHub 연동 정보 없음
              </button>
            )}
            
            <button className="btn-logout" onClick={logout}>
              로그아웃
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}