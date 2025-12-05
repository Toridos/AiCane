import React, { useState, useRef } from 'react'
import { generatePath, generatePathFromCoords } from '../services/api'

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

  // Backend API base (for overlay images from 서버)
  const backendBase =
    (import.meta as any).env?.VITE_API_BASE ||
    ((import.meta as any).env?.DEV ? 'http://localhost:8000' : '')

  // Floor images are served from the frontend의 public 디렉터리 (/public/static/...)
  // 예: public/static/s4_1_nor-1.png, s4_1_nor-2.png ...
  const floorImage = (floor: number) => `/static/s4_1_nor-${floor}.png`

  // click mode: allow user to click image to set start/end coordinates
  const [clickMode, setClickMode] = useState(false)
  const [startCoord, setStartCoord] = useState<{ floor: number; x: number; y: number } | null>(null)
  const [endCoord, setEndCoord] = useState<{ floor: number; x: number; y: number } | null>(null)

  const imgRef = useRef<HTMLImageElement | null>(null)

  const overlayUrls =
  routeData && routeData.overlay
    ? (routeData.overlay as string[]).map((raw) => {
        if (typeof raw !== 'string') return raw

        // 앞뒤 공백/줄바꿈 제거
        const u = raw.trim()

        // "/static/..." 같은 상대경로면 백엔드 베이스를 붙임
        if (u.startsWith('/')) {
          let base = backendBase || ''

          // ✅ 개선안 1: http:// 로 시작하면 https:// 로 강제 변환
          if (base.startsWith('http://')) {
            base = base.replace(/^http:\/\//, 'https://')
          }

          return base + u
        }

        // 이미 "https://..." 같은 절대경로면 그대로 사용
        return u
      })
    : []

  // try to detect which overlay corresponds to which floor by parsing filenames
  const overlayMeta: Array<{url:string,floor:number|null}> = overlayUrls.map(u=>{
    try{
      const m = u.match(/overlay_(\d+)_/)
      return {url:u, floor: m ? parseInt(m[1],10) : null}
    }catch(e){ return {url:u,floor:null} }
  })

  // choose overlay matching current floor when possible
  const displayedOverlay = overlayMeta.find(m=>m.floor===currentFloor)?.url || overlayUrls[0] || null

  const onImageClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if(!clickMode) return
    const img = e.currentTarget
    const rect = img.getBoundingClientRect()
    const scaleX = img.naturalWidth / rect.width
    const scaleY = img.naturalHeight / rect.height
    const x = Math.round((e.clientX - rect.left) * scaleX)
    const y = Math.round((e.clientY - rect.top) * scaleY)
    const f = currentFloor
    if(!startCoord){
      setStartCoord({floor:f,x,y})
    } else if(!endCoord){
      setEndCoord({floor:f,x,y})
    } else {
      // both set -> reset start to new click
      setStartCoord({floor:f,x,y})
      setEndCoord(null)
    }
  }

  const handleGenerateFromCoords = async ()=>{
    if(!startCoord || !endCoord){ setError('출발지/도착지를 먼저 지정하세요'); return }
    setLoading(true); setError(undefined); setRouteData(null)
    try{
      const res = await generatePathFromCoords({ start: startCoord, goal: endCoord })
      if(!res.success) setError('경로를 찾을 수 없습니다')
      else setRouteData(res)
    }catch(err:any){ setError(err.message||String(err)) }
    finally{ setLoading(false) }
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
          <div className="floor-visual" style={{position:'relative'}}>
            {loading ? (
              <div className="placeholder">경로 생성 중...</div>
            ) : routeData ? (
              // show first overlay image if available, otherwise show floor background image
              routeData.overlay && routeData.overlay.length>0 ? (
                <img
                  ref={imgRef}
                  onClick={onImageClick}
                  src={displayedOverlay || floorImage(currentFloor)}
                  crossOrigin="anonymous"
                  onError={(e)=>{
                    const img = e.currentTarget as HTMLImageElement
                    console.warn('Overlay image failed to load:', img.src)
                    try{
                      // 시도1: backendBase가 설정되어 있으면 원래 URL의 path를 가져와서 재시도
                      if(backendBase && img.src.startsWith('http')){
                        const p = new URL(img.src).pathname
                        img.src = backendBase + p
                        console.info('Retrying overlay using backendBase + pathname:', img.src)
                        return
                      }
                    }catch(err){
                      // 무시하고 폴백으로 이동
                    }
                    // 최종 폴백: 바닥 이미지로 대체
                    img.src = floorImage(currentFloor)
                  }}
                  style={{maxWidth:'100%',maxHeight:'100%',cursor: clickMode? 'crosshair':'default'}}
                  alt="overlay"
                />
              ) : (
                <img ref={imgRef} onClick={onImageClick} src={floorImage(currentFloor)} style={{maxWidth:'100%',maxHeight:'100%',cursor: clickMode? 'crosshair':'default'}} alt={`floor ${currentFloor}`} />
              )
            ) : (
              // no route yet: show the static floor image for the selected floor
              <img ref={imgRef} onClick={onImageClick} src={floorImage(currentFloor)} style={{maxWidth:'100%',maxHeight:'100%',cursor: clickMode? 'crosshair':'default'}} alt={`floor ${currentFloor}`} />
            )}

            {/* markers for clicked coords on the currently visible floor */}
            {imgRef.current && imgRef.current.naturalWidth > 0 && startCoord && startCoord.floor===currentFloor && (
              <div className="marker start" style={{left: `${(startCoord.x / imgRef.current!.naturalWidth)*100}%`, top: `${(startCoord.y / imgRef.current!.naturalHeight)*100}%`}} />
            )}
            {imgRef.current && imgRef.current.naturalWidth > 0 && endCoord && endCoord.floor===currentFloor && (
              <div className="marker end" style={{left: `${(endCoord.x / imgRef.current!.naturalWidth)*100}%`, top: `${(endCoord.y / imgRef.current!.naturalHeight)*100}%`}} />
            )}
          </div>
        </div>

        <div className="form-card">
          <label>출발 호수</label>
          <input value={startRoom} onChange={e=>setStartRoom(e.target.value)} placeholder="예: 101" />

          <label>도착 호수</label>
          <input value={endRoom} onChange={e=>setEndRoom(e.target.value)} placeholder="예: 307" />

          <div style={{display:'flex',gap:8,alignItems:'center',marginTop:8}}>
            <button className="generate" onClick={handleGenerate} disabled={!startRoom||!endRoom||loading}>경로 생성 (호수)</button>
            <button className="generate" onClick={()=>{setClickMode(m=>!m); setStartCoord(null); setEndCoord(null)}} style={{background: clickMode? '#f97316':'#6b7280'}}>클릭으로 선택: {clickMode? 'ON':'OFF'}</button>
          </div>

          <div style={{marginTop:8}}>
            <div><strong>클릭 선택 좌표</strong></div>
            <div>출발: {startCoord ? `${startCoord.floor} / ${startCoord.x}, ${startCoord.y}` : '-'}</div>
            <div>도착: {endCoord ? `${endCoord.floor} / ${endCoord.x}, ${endCoord.y}` : '-'}</div>
            <div style={{marginTop:6}}>
              <button className="generate" onClick={handleGenerateFromCoords} disabled={!startCoord || !endCoord || loading}>경로 생성 (좌표)</button>
            </div>
          </div>

          {error && <div style={{color:'crimson',marginTop:8}}>{error}</div>}

          {routeData && (
            <div className="route-info">
              <div>경로 포인트: {routeData.path ? routeData.path.length : 0}</div>
              <div>오버레이 이미지: {overlayUrls.length? overlayUrls.join(', ') : '없음'}</div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
