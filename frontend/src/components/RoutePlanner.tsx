import React, { useState } from 'react'
// api.ts 파일의 위치에 따라 경로가 다를 수 있습니다. (예: '../api' 또는 '../services/api')
// 같은 폴더에 있다면 './api', 상위 폴더에 있다면 '../api' 입니다.
import { generatePath, generatePathFromCoords } from '../services/api' 

export default function RoutePlanner() {
  const [currentFloor, setCurrentFloor] = useState(1)
  const [startRoom, setStartRoom] = useState('')
  const [endRoom, setEndRoom] = useState('')
  
  const [loading, setLoading] = useState(false)
  const [routeData, setRouteData] = useState<any | null>(null)
  const [error, setError] = useState<string | undefined>()

  // 클릭 모드 관련 상태 (좌표 선택용)
  const [clickMode, setClickMode] = useState(false)
  const [startCoord, setStartCoord] = useState<{floor:number, x:number, y:number} | null>(null)
  const [endCoord, setEndCoord] = useState<{floor:number, x:number, y:number} | null>(null)

  // 1. 백엔드 API 주소 가져오기 (환경 변수 또는 기본값)
  const apiBase = (import.meta as any).env?.VITE_API_BASE || 
                  ((import.meta as any).env?.DEV ? 'http://localhost:8000' : '')

  // 2. 층별 지도 이미지 파일명 매핑 (서버의 static 폴더 파일명과 일치해야 함)
  const floorImage = (floor: number) => {
    switch(floor) {
      case 1: return 'static/s4_1-1.png'
      case 2: return 'static/s4_1-2.png'
      case 3: return 'static/s4_1-3.png'
      default: return 'static/s4_1-1.png'
    }
  }

  // 호수 입력으로 경로 생성
  const handleGenerate = async () => {
    if (!startRoom || !endRoom) return
    setLoading(true)
    setError(undefined)
    setRouteData(null)
    try {
      const start = parseInt(startRoom, 10)
      const end = parseInt(endRoom, 10)
      const res = await generatePath({ start_room: start, goal_room: end })
      
      if (!res.success) {
        setError('경로를 찾을 수 없습니다.')
      } else {
        setRouteData(res)
      }
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  // 좌표 입력으로 경로 생성
  const handleGenerateFromCoords = async () => {
    if (!startCoord || !endCoord) return
    setLoading(true)
    setError(undefined)
    setRouteData(null)
    try {
      const res = await generatePathFromCoords({ start: startCoord, goal: endCoord })
      if (!res.success) {
        setError('경로를 찾을 수 없습니다.')
      } else {
        setRouteData(res)
      }
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="planner container">
      <h2>경로 안내</h2>

      <div className="panel">
        <div className="form-card">
          <label>출발 호수</label>
          <input 
            value={startRoom} 
            onChange={e => setStartRoom(e.target.value)} 
            placeholder="예: 101" 
          />

          <label>도착 호수</label>
          <input 
            value={endRoom} 
            onChange={e => setEndRoom(e.target.value)} 
            placeholder="예: 307" 
          />

          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 8 }}>
            <button 
              className="generate" 
              onClick={handleGenerate} 
              disabled={!startRoom || !endRoom || loading}
            >
              {loading ? '생성 중...' : '경로 생성 (호수)'}
            </button>
            <button 
              className="generate" 
              onClick={() => { setClickMode(m => !m); setStartCoord(null); setEndCoord(null) }} 
              style={{ background: clickMode ? '#f97316' : '#6b7280' }}
            >
              클릭으로 선택: {clickMode ? 'ON' : 'OFF'}
            </button>
          </div>

          {/* 좌표 선택 정보 표시 */}
          <div style={{ marginTop: 8, fontSize: '0.9rem', color: '#555' }}>
            <div><strong>클릭 선택 좌표</strong></div>
            <div>출발: {startCoord ? `${startCoord.floor}층 (${startCoord.x}, ${startCoord.y})` : '-'}</div>
            <div>도착: {endCoord ? `${endCoord.floor}층 (${endCoord.x}, ${endCoord.y})` : '-'}</div>
            <div style={{ marginTop: 6 }}>
              <button 
                className="generate" 
                onClick={handleGenerateFromCoords} 
                disabled={!startCoord || !endCoord || loading}
              >
                경로 생성 (좌표)
              </button>
            </div>
          </div>

          {error && <div style={{ color: 'crimson', marginTop: 8 }}>{error}</div>}
        </div>
      </div>

      <div className="panel">
        <div className="floor-controls">
          <button onClick={() => setCurrentFloor(Math.max(1, currentFloor - 1))}>▼ 아래층</button>
          <span>Current Floor: {currentFloor}F</span>
          <button onClick={() => setCurrentFloor(Math.min(3, currentFloor + 1))}>▲ 위층</button>
        </div>

        <div className="floor-visual" style={{ position: 'relative', overflow: 'hidden' }}>
          
          {/* ▼▼▼ [수정됨] 배경 지도 이미지: apiBase 추가 ▼▼▼ */}
          <img 
            src={`${apiBase}/${floorImage(currentFloor)}`} 
            alt={`${currentFloor}F Map`}
            style={{ width: '100%', display: 'block' }}
            crossOrigin="anonymous"
          />

          {/* ▼▼▼ [수정됨] 경로 오버레이 이미지: apiBase 추가 ▼▼▼ */}
          {routeData && routeData.path && (
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
              {(routeData.overlay_urls || routeData.overlay)?.map((url: string, idx: number) => (
                <img 
                  key={idx}
                  src={`${apiBase}${url}`}
                  alt="Route Path"
                  style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                  crossOrigin="anonymous"
                />
              ))}
            </div>
          )}
          
          {/* 클릭 모드 시 마커 표시 (지도 클릭 로직은 생략되었으나 필요한 경우 추가 가능) */}
          {startCoord && startCoord.floor === currentFloor && (
            <div className="marker start" style={{ left: startCoord.x, top: startCoord.y }} />
          )}
          {endCoord && endCoord.floor === currentFloor && (
            <div className="marker end" style={{ left: endCoord.x, top: endCoord.y }} />
          )}

        </div>
      </div>
    </div>
  )
}