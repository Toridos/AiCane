import React, { useState } from 'react'
import Header from './components/Header'
import LandingSection from './components/LandingSection'
import RoutePlanner from './components/RoutePlanner'
import TeamSection from './components/TeamSection'
import './styles.css'

export default function App(){
  const [currentView, setCurrentView] = useState<'landing' | 'planner'>('landing')

  const scrollToPlanner = () => {
    setCurrentView('planner')
    setTimeout(()=>{
      document.getElementById('route-planner')?.scrollIntoView({behavior:'smooth'})
    },100)
  }

  return (
    <div className="app-root">
      <Header onNavigate={setCurrentView} currentView={currentView} />
      <LandingSection onStartPlanning={scrollToPlanner} />
      {currentView === 'planner' && (
        <div id="route-planner">
          <RoutePlanner />
        </div>
      )}
      <TeamSection />
    </div>
  )
}
