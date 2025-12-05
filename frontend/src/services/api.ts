export async function generatePath(body:{start_room:number, goal_room:number}){
  // If VITE_API_BASE is not provided, default to localhost:8000 in dev mode
  const metaEnv = (import.meta as any).env ?? {};
  const base = metaEnv.VITE_API_BASE || (metaEnv.DEV ? 'http://localhost:8000' : '')
  const url = base + '/api/generate-path'
  const resp = await fetch(url,{
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })
  if(!resp.ok) throw new Error(`Server error ${resp.status}`)
  return resp.json()
}
export async function generatePathFromCoords(body:{start:{floor:number,x:number,y:number}, goal:{floor:number,x:number,y:number}}){
  const metaEnv = (import.meta as any).env ?? {};
  const base = metaEnv.VITE_API_BASE || (metaEnv.DEV ? 'http://localhost:8000' : '')
  const url = base + '/api/generate-path-coords'
  const resp = await fetch(url,{
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })
  if(!resp.ok) throw new Error(`Server error ${resp.status}`)
  return resp.json()
}

// Pi에게 경로 전달
export async function sendRouteToPi(piIP: string, routeJson: any) {
  try {
    const url = `http://${piIP}:8001/load-route`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ route: routeJson }),
    });
    console.log("📤 Pi로 경로 전송 성공:", await res.json());
    return true;
  } catch (err) {
    console.error("❌ Pi로 전송 실패:", err);
    return false;
  }
}

