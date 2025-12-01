import React from 'react'

interface Props{ onStartPlanning: ()=>void }

export default function LandingSection({onStartPlanning}:Props){
  return (
    <section className="landing">
      <div className="hero container">
        <div className="badge">실내 경로 안내 시스템</div>
        <h1>AiCane Indoor Route Planner</h1>
        <p>건물 내부에서 목적지까지 가장 빠른 경로를 찾아드립니다.</p>
        <button className="cta" onClick={onStartPlanning}>AiCane 주행하기 →</button>
      </div>
      <div className="features container">
        <div className="feature">정확한 경로 안내</div>
        <div className="feature">빠른 처리 속도</div>
        <div className="feature">사용자 친화적</div>
      </div>
    </section>
  )
}
