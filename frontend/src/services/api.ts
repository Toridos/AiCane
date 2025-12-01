export async function generatePath(body:{start_room:number, goal_room:number}){
  // If VITE_API_BASE is not provided, default to localhost:8000 in dev mode
  const base = import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? 'http://localhost:8000' : '')
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
  const base = import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? 'http://localhost:8000' : '')
  const url = base + '/api/generate-path-coords'
  const resp = await fetch(url,{
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  })
  if(!resp.ok) throw new Error(`Server error ${resp.status}`)
  return resp.json()
}
