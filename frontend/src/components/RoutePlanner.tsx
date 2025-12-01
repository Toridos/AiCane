import React, { useState } from 'react'
import { generatePath } from '../services/api'

export default function RoutePlanner(){
  const [currentFloor, setCurrentFloor] = useState(1)
  const [startRoom,setStartRoom]=useState('')
  const [endRoom,setEndRoom]=useState('')
  const [loading,setLoading]=useState(false)
  const [routeData,setRouteData]=useState<any|null>(null)
  const [error,setError]=useState<string|undefined>()

  const handleGenerate=async()=>{
    if(!startRoom || !endRoom) return
    setLoading(true)
    setError(undefined)
    setRouteData(null)
    try{
      const start = parseInt(startRoom,10)
      const end = parseInt(endRoom,10)
      const res = await generatePath({start_room:start, goal_room:end})
      if(!res.success) {
        setError('경로를 찾을 수 없습니다')
      } else {
        setRouteData(res)
      }
    }catch(err:any){
      setError(err.message||String(err))
    }finally{
      setLoading(false)
    }
  }

  // Floor image base: prefer configured API base, otherwise default to backend in dev
  const apiBase = (import.meta as any).env?.VITE_API_BASE || ((import.meta as any).env?.DEV ? 'http://localhost:8000' : '')
  const floorImage = (floor: number) => {
    // map 1-> static/s4-1_floor1.png, etc
    const name = `/static/s4-1_floor${floor}.png`
    return apiBase ? `${apiBase}${name}` : name
  }

  return (
    <section className="route-planner container">
      <div className="planner-grid">
        <div className="floor-card">
          <div className="floor-controls">
            <button onClick={()=>setCurrentFloor(f=>Math.max(1,f-1))} disabled={currentFloor===1}>Prev</button>
            <div className="floor-indicator">{currentFloor}층</div>
            <button onClick={()=>setCurrentFloor(f=>f+1)} disabled={currentFloor===10}>Next</button>
          </div>
          <div className="floor-visual">
            {loading ? (
              <div className="placeholder">경로 생성 중...</div>
            ) : routeData ? (
              // show first overlay image if available, otherwise show floor background image
              routeData.overlay && routeData.overlay.length>0 ? (
                <img src={routeData.overlay[0]} style={{maxWidth:'100%',maxHeight:'100%'}} alt="overlay" />
              ) : (
                <img src={floorImage(currentFloor)} style={{maxWidth:'100%',maxHeight:'100%'}} alt={`floor ${currentFloor}`} />
              )
            ) : (
              // no route yet: show the static floor image for the selected floor
              <img src={floorImage(currentFloor)} style={{maxWidth:'100%',maxHeight:'100%'}} alt={`floor ${currentFloor}`} />
            )}
          </div>
        </div>

        <div className="form-card">
          <label>출발 호수</label>
          <input value={startRoom} onChange={e=>setStartRoom(e.target.value)} placeholder="예: 101" />

          <label>도착 호수</label>
          <input value={endRoom} onChange={e=>setEndRoom(e.target.value)} placeholder="예: 307" />

          <button className="generate" onClick={handleGenerate} disabled={!startRoom||!endRoom||loading}>경로 생성</button>

          {error && <div style={{color:'crimson',marginTop:8}}>{error}</div>}

          {routeData && (
            <div className="route-info">
              <div>경로 포인트: {routeData.path ? routeData.path.length : 0}</div>
              <div>오버레이 이미지: {routeData.overlay ? routeData.overlay.join(', ') : '없음'}</div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
