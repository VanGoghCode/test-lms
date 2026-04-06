'use client'

import { useState, useEffect } from 'react'

interface Assignment {
  id: number
  title: string
  course_id: number
  course_name: string
  due_date: string
  status: string
  grade?: number
}

export default function Assignments() {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [filter, setFilter] = useState('')

  useEffect(() => {
    const params = filter ? `?status=${filter}` : ''
    fetch(`http://localhost:8000/api/users/1/assignments${params}`)
      .then(r => r.json())
      .then(setAssignments)
  }, [filter])

  const statusBadge = (status: string) => {
    const classes: Record<string, string> = {
      pending: 'badge-warning',
      submitted: 'badge-success',
      graded: 'badge-success'
    }
    return classes[status] || 'badge-warning'
  }

  return (
    <>
      <h1>Assignments</h1>
      <p className="subtitle">Track your assignments and grades</p>

      <div className="filters">
        <button className={`filter-btn ${!filter ? 'active' : ''}`} onClick={() => setFilter('')}>All</button>
        <button className={`filter-btn ${filter === 'pending' ? 'active' : ''}`} onClick={() => setFilter('pending')}>Pending</button>
        <button className={`filter-btn ${filter === 'submitted' ? 'active' : ''}`} onClick={() => setFilter('submitted')}>Submitted</button>
        <button className={`filter-btn ${filter === 'graded' ? 'active' : ''}`} onClick={() => setFilter('graded')}>Graded</button>
      </div>

      <div className="assignment-list">
        {assignments.map(assignment => (
          <div key={assignment.id} className="assignment-item">
            <div className="assignment-info">
              <h3>{assignment.title}</h3>
              <p className="assignment-course">{assignment.course_name}</p>
              <p className="assignment-due">Due: {assignment.due_date}</p>
            </div>
            <div className="assignment-right">
              {assignment.grade && <span className="grade">{assignment.grade}%</span>}
              <span className={`badge ${statusBadge(assignment.status)}`}>{assignment.status}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}