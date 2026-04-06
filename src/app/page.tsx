'use client'
import { useAuth } from './auth-context'
import { useEffect, useState } from 'react'

interface Enrollment {
  id: number
  course_id: number
  user_id: number
  progress: number
  enrolled_at: string
  course: any
}

interface Assignment {
  id: number
  title: string
  course_id: number
  course_name: string
  due_date: string
  status: string
  grade?: number
}

export default function Home() {
  const { user, token, isLoading: authLoading } = useAuth()
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    
    if (!user || !token) {
      setLoading(false)
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/users/${user.id}/enrollments`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setEnrollments)
      .catch(console.error)

    fetch(`${baseUrl}/api/users/${user.id}/assignments`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setAssignments)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user, token, authLoading])

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  if (!user) {
    return (
      <>
        <h1>Welcome to LMS</h1>
        <p className="subtitle">Start your learning journey today</p>
        <div className="grid">
          <a href="/login" className="card">
            <div className="card-thumbnail" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              L
            </div>
            <div className="card-body">
              <h3 className="card-title">Sign In</h3>
              <p className="card-meta">Access your courses and track progress</p>
            </div>
          </a>
          <a href="/register" className="card">
            <div className="card-thumbnail" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
              R
            </div>
            <div className="card-body">
              <h3 className="card-title">Create Account</h3>
              <p className="card-meta">Join our learning community</p>
            </div>
          </a>
        </div>
      </>
    )
  }

  const pendingAssignments = assignments.filter((a) => a.status === 'pending').length

  return (
    <>
      <h1>Welcome back, {user.name.split(' ')[0]}</h1>
      <p className="subtitle">Continue your learning journey</p>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-value">{enrollments.length}</div>
          <div className="stat-label">Enrolled Courses</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{pendingAssignments}</div>
          <div className="stat-label">Pending Assignments</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {Math.round(enrollments.reduce((acc: number, e: any) => acc + e.progress, 0) / enrollments.length || 0)}%
          </div>
          <div className="stat-label">Average Progress</div>
        </div>
      </div>

      <h2>Continue Learning</h2>
      <div className="grid">
        {enrollments.slice(0, 3).map((enrollment: any) => (
          <a href={`/courses/${enrollment.course_id}`} key={enrollment.id} className="card">
            <div className="card-thumbnail" style={{ background: enrollment.course.thumbnail }}>
              {enrollment.course.title.charAt(0)}
            </div>
            <div className="card-body">
              <h3 className="card-title">{enrollment.course.title}</h3>
              <p className="card-meta">{enrollment.course.instructor.name}</p>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${enrollment.progress}%` }} />
              </div>
            </div>
          </a>
        ))}
      </div>
    </>
  )
}