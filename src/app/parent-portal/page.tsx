'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '../auth-context'
import { useRouter } from 'next/navigation'

interface Child {
  child_id: number
  child_name: string
  child_email: string
  child_avatar: string
  relation: string
  linked_at: string
}

interface Dashboard {
  child_id: number
  child_name: string
  child_avatar: string
  enrolled_courses: number
  completed_courses: number
  average_progress: number
  upcoming_assignments: number
  overdue_assignments: number
  recent_grades: Array<{
    assignment_title: string
    course_name: string
    grade: number
    max_grade: number
    submitted_at: string
  }>
  recent_activity: Array<{
    type: string
    course_name: string
    progress: number
    updated_at: string
  }>
}

export default function ParentPortalPage() {
  const { user, token } = useAuth()
  const router = useRouter()
  const [children, setChildren] = useState<Child[]>([])
  const [selectedChild, setSelectedChild] = useState<number | null>(null)
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [showLinkForm, setShowLinkForm] = useState(false)
  const [childEmail, setChildEmail] = useState('')
  const [relation, setRelation] = useState('parent')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    fetchChildren()
  }, [user, router])

  useEffect(() => {
    if (selectedChild) {
      fetchDashboard(selectedChild)
    }
  }, [selectedChild])

  const fetchChildren = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/parent/children', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setChildren(data)
        if (data.length > 0 && !selectedChild) {
          setSelectedChild(data[0].child_id)
        }
      }
    } catch (error) {
      console.error('Failed to fetch children:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchDashboard = async (childId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/parent/dashboard/${childId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setDashboard(data)
      }
    } catch (error) {
      console.error('Failed to fetch dashboard:', error)
    }
  }

  const handleLinkChild = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')

    try {
      const response = await fetch('http://localhost:8000/api/parent/link-child', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ child_email: childEmail, relation })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to link child')
      }

      setMessage(`Verification request sent to ${data.child_name}. They will need to verify using code: ${data.verification_code}`)
      setChildEmail('')
      setShowLinkForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link child')
    }
  }

  const handleUnlink = async (childId: number) => {
    if (!confirm('Are you sure you want to unlink this child?')) return

    try {
      const response = await fetch(`http://localhost:8000/api/parent/unlink/${childId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        setChildren(children.filter(c => c.child_id !== childId))
        if (selectedChild === childId) {
          setSelectedChild(children.length > 1 ? children[0].child_id : null)
        }
      }
    } catch (error) {
      console.error('Failed to unlink child:', error)
    }
  }

  if (loading) {
    return <div className="loading">Loading parent portal...</div>
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Parent Portal</h1>
        <p>Monitor your child's learning progress</p>
      </div>

      {message && <div className="success-message">{message}</div>}
      {error && <div className="error-message">{error}</div>}

      <div className="parent-portal-layout">
        <div className="children-sidebar">
          <div className="sidebar-header">
            <h2>My Children</h2>
            <button className="btn-primary" onClick={() => setShowLinkForm(!showLinkForm)}>
              + Add Child
            </button>
          </div>

          {showLinkForm && (
            <form className="link-form" onSubmit={handleLinkChild}>
              <div className="form-group">
                <label>Child's Email</label>
                <input
                  type="email"
                  value={childEmail}
                  onChange={(e) => setChildEmail(e.target.value)}
                  placeholder="child@example.com"
                  required
                />
              </div>
              <div className="form-group">
                <label>Relation</label>
                <select value={relation} onChange={(e) => setRelation(e.target.value)}>
                  <option value="parent">Parent</option>
                  <option value="guardian">Guardian</option>
                </select>
              </div>
              <button type="submit" className="btn-primary">Send Request</button>
            </form>
          )}

          {children.length === 0 ? (
            <div className="empty-children">
              <p>No children linked yet</p>
              <p className="hint">Click "Add Child" to link your child's account</p>
            </div>
          ) : (
            <div className="children-list">
              {children.map(child => (
                <div
                  key={child.child_id}
                  className={`child-card ${selectedChild === child.child_id ? 'active' : ''}`}
                  onClick={() => setSelectedChild(child.child_id)}
                >
                  <div className="child-avatar">{child.child_avatar}</div>
                  <div className="child-info">
                    <h3>{child.child_name}</h3>
                    <span className="relation">{child.relation}</span>
                  </div>
                  <button
                    className="btn-icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleUnlink(child.child_id)
                    }}
                    title="Unlink"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="dashboard-content">
          {!dashboard ? (
            <div className="empty-state">
              <h2>Select a child to view their progress</h2>
              <p>Choose a child from the sidebar to see their learning dashboard</p>
            </div>
          ) : (
            <>
              <div className="dashboard-header">
                <div className="child-profile">
                  <div className="avatar-large">{dashboard.child_avatar}</div>
                  <h2>{dashboard.child_name}'s Progress</h2>
                </div>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">📚</div>
                  <div className="stat-value">{dashboard.enrolled_courses}</div>
                  <div className="stat-label">Enrolled Courses</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">✅</div>
                  <div className="stat-value">{dashboard.completed_courses}</div>
                  <div className="stat-label">Completed</div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon">📊</div>
                  <div className="stat-value">{dashboard.average_progress}%</div>
                  <div className="stat-label">Average Progress</div>
                </div>
                <div className="stat-card warning">
                  <div className="stat-icon">⏰</div>
                  <div className="stat-value">{dashboard.upcoming_assignments}</div>
                  <div className="stat-label">Due Soon</div>
                </div>
                <div className="stat-card danger">
                  <div className="stat-icon">⚠️</div>
                  <div className="stat-value">{dashboard.overdue_assignments}</div>
                  <div className="stat-label">Overdue</div>
                </div>
              </div>

              <div className="dashboard-sections">
                <div className="section">
                  <h3>Recent Grades</h3>
                  {dashboard.recent_grades.length === 0 ? (
                    <p className="no-data">No grades yet</p>
                  ) : (
                    <div className="grades-list">
                      {dashboard.recent_grades.map((grade, idx) => (
                        <div key={idx} className="grade-item">
                          <div className="grade-info">
                            <h4>{grade.assignment_title}</h4>
                            <span className="course-name">{grade.course_name}</span>
                          </div>
                          <div className="grade-score">
                            <span className="score">{grade.grade}/{grade.max_grade}</span>
                            <span className="percentage">
                              {Math.round((grade.grade / grade.max_grade) * 100)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="section">
                  <h3>Recent Activity</h3>
                  {dashboard.recent_activity.length === 0 ? (
                    <p className="no-data">No recent activity</p>
                  ) : (
                    <div className="activity-list">
                      {dashboard.recent_activity.map((activity, idx) => (
                        <div key={idx} className="activity-item">
                          <div className="activity-icon">📖</div>
                          <div className="activity-info">
                            <h4>{activity.course_name}</h4>
                            <div className="progress-bar small">
                              <div className="progress-fill" style={{ width: `${activity.progress}%` }} />
                            </div>
                            <span className="progress-text">{activity.progress}% complete</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="quick-actions">
                <button
                  className="btn-secondary"
                  onClick={() => router.push(`/parent-portal/child/${selectedChild}/courses`)}
                >
                  View All Courses
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => router.push(`/parent-portal/child/${selectedChild}/assignments`)}
                >
                  View Assignments
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
