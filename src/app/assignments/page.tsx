'use client'
import { useAuth } from '../auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Assignment {
  id: number
  title: string
  course_id: number
  course_name: string
  description: string
  due_date: string
  status: string
  grade?: number
  max_grade: number
}

export default function AssignmentsPage() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/users/${user.id}/assignments`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => {
        if (filter !== 'all') {
          data = data.filter((a: Assignment) => a.status === filter)
        }
        setAssignments(data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user, token, authLoading, router, filter])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'graded': return 'badge-success'
      case 'submitted': return 'badge-warning'
      default: return 'badge-error'
    }
  }

  const isOverdue = (dueDate: string) => {
    return new Date(dueDate) < new Date()
  }

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <>
      <h1>My Assignments</h1>
      <p className="subtitle">View and submit your course assignments</p>

      <div className="filters">
        <button className={`filter-btn ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>All</button>
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
              <p className="assignment-due">
                Due: {assignment.due_date}
                {assignment.status === 'pending' && isOverdue(assignment.due_date) && (
                  <span className="overdue-badge"> - Overdue!</span>
                )}
              </p>
            </div>
            <div className="assignment-right">
              <span className={`badge ${getStatusBadge(assignment.status)}`}>{assignment.status}</span>
              {assignment.grade !== undefined && assignment.grade !== null && (
                <span className="grade">{assignment.grade}/{assignment.max_grade}</span>
              )}
              {assignment.status === 'pending' && (
                <a href={`/assignments/${assignment.id}/submit`} className="btn-primary">Submit</a>
              )}
              {assignment.status === 'submitted' && (
                <a href={`/assignments/${assignment.id}/submit`} className="btn-secondary">View Submission</a>
              )}
            </div>
          </div>
        ))}
        {assignments.length === 0 && (
          <p className="empty-state">No assignments found</p>
        )}
      </div>
    </>
  )
}