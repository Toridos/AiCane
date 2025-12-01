import React from 'react'

const members = [
  {name:'김다민', role:'AI Developer'},
  {name:'박조현', role:'Backend Developer'},
  {name:'배수연', role:'Hardware Engineer'}
]

export default function TeamSection(){
  return (
    <section id="team-section" className="team container">
      <h2>About Our Members</h2>
      <p>AiCane 프로젝트를 함께 만들어가는 열정적인 팀원들을 소개합니다</p>
      <div className="team-grid">
        {members.map((m,i)=> (
          <div className="member" key={i}>
            <div className="avatar">{m.name.charAt(0)}</div>
            <h3>{m.name}</h3>
            <p className="role">{m.role}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
