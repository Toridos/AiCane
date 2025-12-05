import React, { useState, useRef, useEffect } from 'react'
import { generatePath, generatePathFromCoords } from '../services/api'

export default function RoutePlanner(){
  const [currentFloor, setCurrentFloor] = useState(1)
  const [startRoom,setStartRoom]=useState('')
  const [endRoom,setEndRoom]=useState('')
  const [loading,setLoading]=useState(false)
  const [routeData,setRouteData]=useState<any|null>(null)
  const [error,setError]=useState<string|undefined>()

  // -----------------------------------------------------------
  // [설정 1] 백엔드 주소 (Ngrok)
  // -----------------------------------------------------------
  const backendBase = "https://unhappi-shon-unmellifluously.ngrok-free.dev"; 

  const floorImage = (floor: number) => `static/s4_1_nor-${floor}.png`

  const [clickMode, setClickMode] = useState(false)
  const [startCoord, setStartCoord] = useState<{ floor: number; x: number; y: number } | null>(null)
  const [endCoord, setEndCoord] = useState<{ floor: number; x: number; y: number } | null>(null)
  const imgRef = useRef<HTMLImageElement | null>(null)

  // -----------------------------------------------------------
  // [설정 2] 이미지 URL 정리 (HTTPS 강제)
  // -----------------------------------------------------------
  const overlayUrls = (routeData && routeData.overlay)
  ? (routeData.overlay as string[]).map((raw) => {
      if (typeof raw !== 'string') return raw
      let u = raw.trim()
      if (u.startsWith('/')) return backendBase + u
      if (u.startsWith('http://')) return u.replace('http://', 'https://')
      return u
    })
  : []

  const overlayMeta: Array<{url:string,floor:number|null}> = overlayUrls.map(u=>{
    try{
      const m = u.match(/overlay_(\d+)_/)
      return {url:u, floor: m ? parseInt(m[1],10) : null}
    }catch(e){ return {url:u,floor:null} }
  })

  // 원본 오버레이 URL
  const displayedOverlayUrl = overlayMeta.find(m=>m.floor===currentFloor)?.url || overlayUrls[0] || null

  // -----------------------------------------------------------
  // [핵심 해결책] Ngrok 경고 우회용 이미지 로더
  // 일반 <img> 태그 대신 fetch로 데이터를 받아옵니다.
  // -----------------------------------------------------------
  const [secureOverlayBlob, setSecureOverlayBlob] = useState<string | null>(null);

  useEffect(() => {
    if (!displayedOverlayUrl) {
      setSecureOverlayBlob(null);
      return;
    }

    // 로컬 이미지나 data URL이면 그냥 보여줌
    if (!displayedOverlayUrl.startsWith('http')) {
        setSecureOverlayBlob(displayedOverlayUrl);
        return;
    }

    // Ngrok URL이면 헤더를 추가해서 fetch
    const fetchImage = async () => {
      try {
        const response = await fetch(displayedOverlayUrl, {
          headers: new Headers({
            // ★ 이 헤더가 있어야 Ngrok 경고창이 안 뜹니다! ★
            "ngrok-skip-browser-warning": "69420", 
          }),
        });
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        setSecureOverlayBlob(objectUrl);
      } catch (err) {
        console.error("Failed to load secure image", err);
        setSecureOverlayBlob(null);
      }
    };

    fetchImage();
  }, [displayedOverlayUrl]); // URL이 바뀔 때마다 실행


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

  const handleGenerate = async()=>{
    if(!startRoom || !endRoom) return
    setLoading(true); setError(undefined); setRouteData(null); setSecureOverlayBlob(null);
    try{
      const start = parseInt(startRoom,10)
      const end = parseInt(endRoom,10)
      const res = await generatePath({start_room:start, goal_room:end})
      if(!res.success) setError('경로를 찾을 수 없습니다')
      else setRouteData(res)
    }catch(err:any){ setError(err.message||String(err)) }
    finally{ setLoading(false) }
  }

  const handleGenerateFromCoords = async ()=>{
    if(!startCoord || !endCoord){ setError('출발지/도착지를 먼저 지정하세요'); return }
    setLoading(true); setError(undefined); setRouteData(null); setSecureOverlayBlob(null);
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
                <div style={{position:'relative', width:'100%', height:'100%'}}>
                    {/* 1. 배경 지도 */}
                    <img 
                        ref={imgRef} 
                        onClick={onImageClick} 
                        src={floorImage(currentFloor)} 
                        style={{width:'100%', display:'block', cursor: clickMode? 'crosshair':'default'}} 
                        alt={`floor ${currentFloor}`} 
                    />
                    
                    {/* 2. 오버레이 (보안 패치된 Blob 이미지 사용) */}
                    {secureOverlayBlob && (
                        <img 
                            src={secureOverlayBlob}
                            style={{
                                position: 'absolute', 
                                top: 0, 
                                left: 0, 
                                width: '100%', 
                                height: '100%', 
                                pointerEvents: 'none'
                            }} 
                            alt="route overlay"
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
        </div>
      </div>
    </section>
  )
}