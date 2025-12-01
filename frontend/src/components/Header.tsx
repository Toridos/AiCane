import React, { useState } from 'react'

interface HeaderProps{
  onNavigate: (v:'landing'|'planner') => void
  currentView: 'landing'|'planner'
}

export default function Header({onNavigate}:HeaderProps){
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const scrollToSection = (id:string)=>{
    document.getElementById(id)?.scrollIntoView({behavior:'smooth'})
    setMobileMenuOpen(false)
  }
  return (
    <header className="site-header">
      <div className="container">
        <div className="brand" onClick={()=>onNavigate('landing')}>AiCane</div>
        <nav className="nav-desktop">
          <button onClick={()=>onNavigate('landing')}>홈</button>
          <button onClick={()=>onNavigate('planner')}>경로 생성</button>
          <button onClick={()=>scrollToSection('team-section')}>팀 소개</button>
        </nav>
        <button className="nav-mobile-btn" onClick={()=>setMobileMenuOpen(!mobileMenuOpen)}>
          ☰
        </button>
      </div>
      {mobileMenuOpen && (
        <nav className="nav-mobile">
          <button onClick={()=>{onNavigate('landing'); setMobileMenuOpen(false)}}>홈</button>
          <button onClick={()=>{onNavigate('planner'); setMobileMenuOpen(false)}}>경로 생성</button>
          <button onClick={()=>scrollToSection('team-section')}>팀 소개</button>
        </nav>
      )}
    </header>
  )
}
