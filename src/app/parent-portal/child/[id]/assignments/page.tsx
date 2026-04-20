'use client'
import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '../../../auth-context'

interface Assignment {
  assignment_id: number
  title: string
  course_name: string
  due_date: string
  max_grade: number
  status: string
  grade: number | null
  feedback: string | null
  submitted_at: string | null
}

export default function ParentChildAssignmentsPage() {
  const params = useParams()
  const router = useRouter()
  const { user, token } = useAuth()
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    fetchAssignments()
  }, [user, router])

  const fetchAssignments = async (status?: string) => {
    try {
      const url = status && status !== 'all'
        ? `http://localhost:8000/api/parent/child/${params.id}/assignments?status=${status}`
        : `http://localhost:8000/api/parent/child/${params.id}/assignments`
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAssignments(data)
      }
    } catch (error) {
      console.error('Failed to fetch assignments:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter)
    fetchAssignments(newFilter)
  }

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      pending: 'badge-warning',
      submitted: 'badge-info',
      graded: 'badge-success'
    }
    return badges[status] || ''
  }

  if (loading) {
    return <div className="loading">Loading assignments...</div>
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <button className="btn-back" onClick={() => router.push('/parent-portal')}>
          ← Back to Dashboard
        </button>
        <h1>Child's Assignments</h1>
      </div>

      <div className="filter-tabs">
        <button 
          className={filter === 'all' ? 'active' : ''}
          onClick={() => handleFilterChange('all')}
        >
          All ({assignments.length})
        </button>
        <button 
          className={filter === 'pending' ? 'active' : ''}
          onClick={() => handleFilterChange('pending')}
        >
          Pending
        </button>
        <button 
          className={filter === 'submitted' ? 'active' : ''}
          onClick={() => handleFilterChange('submitted')}
        >
          Submitted
        </button>
        <button 
          className={filter === 'graded' ? 'active' : ''}
          onClick={() => handleFilterChange('graded')}
        >
          Graded
        </button>
      </div>

      {assignments.length === 0 ? (
        <div className="empty-state">
          <h2>No assignments found</h2>
          <p>No assignments match the selected filter</p>
        </div>
      ) : (
        <div className="assignments-table">
          <table>
            <thead>
              <tr>
                <th>Assignment</th>
                <th>Course</th>
                <th>Due Date</th>
                <th>Status</th>
                <th>Grade</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {assignments.map(assignment => (
                <tr key={assignment.assignment_id}>
                  <td className="assignment-title">{assignment.title}</td>
                  <td>{assignment.course_name}</td>
                  <td>{assignment.due_date}</td>
                  <td>
                    <span className={`badge ${getStatusBadge(assignment.status)}`}>
                      {assignment.status}
                    </span>
                  </td>
                  <td>
                    {assignment.grade !== null ? (
                      <div className="grade-display">
                        <span className="grade">{assignment.grade}/{assignment.max_grade}</span>
                        <span className="percentage">
                          {Math.round((assignment.grade / assignment.max_grade) * 100)}%
                        </span>
                      </div>
                    ) : (
                      <span className="no-grade">-</span>
                    )}
                  </td>
                  <td>{assignment.submitted_at || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {assignments.some(a => a.feedback) && (
        <div className="feedback-section">
          <h2>Recent Feedback</h2>
          <div className="feedback-list">
            {assignments
              .filter(a => a.feedback)
              .map(assignment => (
                <div key={assignment.assignment_id} className="feedback-item">
                  <h4>{assignment.title}</h4>
                  <p className="feedback-text">{assignment.feedback}</p>
                  <span className="grade-badge">Grade: {assignment.grade}/{assignment.max_grade}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
