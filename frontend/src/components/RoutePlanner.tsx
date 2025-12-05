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

  // ----------------------------------------------------------------
  // [설정 1] 백엔드 주소 하드코딩 (환경변수 문제 원천 차단)
  // ★ 본인의 Ngrok 주소가 맞는지 확인하세요!
  // ----------------------------------------------------------------
  const backendBase = "https://unhappi-shon-unmellifluously.ngrok-free.dev"; 

  // 배경 이미지 파일명
  const floorImage = (floor: number) => `static/s4_1_nor-${floor}.png`

  const [clickMode, setClickMode] = useState(false)
  const [startCoord, setStartCoord] = useState<{ floor: number; x: number; y: number } | null>(null)
  const [endCoord, setEndCoord] = useState<{ floor: number; x: number; y: number } | null>(null)
  const imgRef = useRef<HTMLImageElement | null>(null)

  // ----------------------------------------------------------------
  // [설정 2] 오버레이 이미지 주소 생성 (HTTPS 강제 변환)
  // ----------------------------------------------------------------
  const overlayUrls = (routeData && routeData.overlay)
  ? (routeData.overlay as string[]).map((raw) => {
      if (typeof raw !== 'string') return raw
      let u = raw.trim()

      // 1) "/static/..." 처럼 상대경로면 -> 백엔드 주소(HTTPS) 붙이기
      if (u.startsWith('/')) {
          return backendBase + u
      }
      
      // 2) "http://" 로 시작하면 -> "무조건 https://"로 강제 치환
      // (이게 있어야 Vercel에서 차단 안 당함!)
      if (u.startsWith('http://')) {
          return u.replace('http://', 'https://')
      }
      return u
    })
  : []

  // 층수 파싱
  const overlayMeta: Array<{url:string,floor:number|null}> = overlayUrls.map(u=>{
    try{
      const m = u.match(/overlay_(\d+)_/)
      return {url:u, floor: m ? parseInt(m[1],10) : null}
    }catch(e){ return {url:u,floor:null} }
  })

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
            <button onClick={()=>setCurrentFloor(f=>Math.min(3,f+1))} disabled={currentFloor===3}>Next</button>
          </div>
          
          <div className="floor-visual" style={{position:'relative', border:'1px solid #ddd'}}>
            {loading ? (
              <div className="placeholder" style={{padding:'20px', textAlign:'center'}}>경로 생성 중...</div>
            ) : (
                // ----------------------------------------------------------------
                // [설정 3] 겹쳐 그리기 (Layering)
                // ----------------------------------------------------------------
                <div style={{position:'relative', width:'100%', height:'100%'}}>
                    {/* 1. 배경 지도 (항상 표시) */}
                    <img 
                        ref={imgRef} 
                        onClick={onImageClick} 
                        src={floorImage(currentFloor)} 
                        style={{width:'100%', display:'block', cursor: clickMode? 'crosshair':'default'}} 
                        alt={`floor ${currentFloor}`} 
                    />
                    
                    {/* 2. 오버레이 (경로 데이터가 있을 때만 위에 표시) */}
                    {displayedOverlay && (
                        <img 
                            src={displayedOverlay}
                            style={{
                                position: 'absolute', 
                                top: 0, 
                                left: 0, 
                                width: '100%', 
                                height: '100%', 
                                pointerEvents: 'none'
                            }} 
                            alt="route overlay"
                            crossOrigin="anonymous"
                            // 에러가 나도 배경 지도로 바꾸지 않고 그냥 콘솔에만 찍음
                            onError={(e) => console.error("Overlay failed:", e.currentTarget.src)}
                        />
                    )}
                </div>
            )}

            {/* 좌표 마커 */}
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
            <div>출발: {startCoord ? `${startCoord.floor}층 (${startCoord.x}, ${startCoord.y})` : '-'}</div>
            <div>도착: {endCoord ? `${endCoord.floor}층 (${endCoord.x}, ${endCoord.y})` : '-'}</div>
            <div style={{marginTop:6}}>
              <button className="generate" onClick={handleGenerateFromCoords} disabled={!startCoord || !endCoord || loading}>경로 생성 (좌표)</button>
            </div>
          </div>

          {error && <div style={{color:'crimson',marginTop:8}}>{error}</div>}

          {routeData && (
            <div className="route-info">
               {/* 디버깅용: 실제 적용된 주소 확인 */}
              <div style={{fontSize:'0.7em', color:'#888', wordBreak:'break-all'}}>
                 {overlayUrls.length > 0 ? overlayUrls[0] : ''}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}