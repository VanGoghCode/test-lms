'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../auth-context'

interface AlertDueItem {
  assignment_id: number
  title: string
  due_date: string
  status: string
}

interface LearningAlert {
  course_id: number
  course_title: string
  course_category: string
  instructor_name: string
  student_id: number
  student_name: string
  progress_percent: number
  submitted_assignments: number
  graded_assignments: number
  overdue_assignments: number
  due_soon_assignments: number
  average_grade?: number | null
  best_quiz_score?: number | null
  risk_score: number
  priority: 'low' | 'medium' | 'high'
  reasons: string[]
  next_steps: string[]
  due_items: AlertDueItem[]
}

interface AlertsPayload {
  scope: string
  generated_at: string
  summary: {
    tracked_items: number
    needs_attention: number
    high_priority: number
    average_progress: number
    overdue_assignments: number
  }
  alerts: LearningAlert[]
}

function priorityBadge(priority: LearningAlert['priority']) {
  if (priority === 'high') {
    return 'badge-error'
  }

  if (priority === 'medium') {
    return 'badge-warning'
  }

  return 'badge-success'
}

function priorityLabel(priority: LearningAlert['priority']) {
  if (priority === 'high') {
    return 'High priority'
  }

  if (priority === 'medium') {
    return 'Needs attention'
  }

  return 'On track'
}

function formatPercent(value: number) {
  return `${Math.round(value)}%`
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

export default function AlertsPage() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [payload, setPayload] = useState<AlertsPayload | null>(null)

  useEffect(() => {
    if (authLoading) {
      return
    }

    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/users/${user.id}/alerts`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || 'Failed to load alerts')
        }

        setPayload(data)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authLoading, router, token, user])

  const alerts = useMemo(() => {
    if (!payload) {
      return []
    }

    return [...payload.alerts].sort((left, right) => right.risk_score - left.risk_score)
  }, [payload])

  if (authLoading || loading) {
    return <p>Loading alerts...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  if (!payload) {
    return <p className="subtitle">No alerts available.</p>
  }

  const scopeLabel = payload.scope === 'admin'
    ? 'Platform-wide learning overview'
    : payload.scope === 'instructor'
      ? 'Courses you manage'
      : 'Your enrolled courses'

  return (
    <div className="alerts-page">
      <div className="page-header alerts-hero">
        <div>
          <h1>Learning Alerts</h1>
          <p className="subtitle">
            {scopeLabel}. {payload.summary.needs_attention} tracked items need attention and {payload.summary.high_priority} are high priority.
          </p>
          <div className="alerts-meta">
            <span className="alert-chip">Updated {payload.generated_at}</span>
            <span className="alert-chip">{payload.summary.tracked_items} tracked items</span>
          </div>
        </div>
        <a href="/my-learning" className="btn-secondary">Back to My Learning</a>
      </div>

      <section className="stats">
        <div className="stat-card">
          <div className="stat-value">{payload.summary.tracked_items}</div>
          <div className="stat-label">Tracked Items</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{payload.summary.needs_attention}</div>
          <div className="stat-label">Need Attention</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{payload.summary.overdue_assignments}</div>
          <div className="stat-label">Overdue Assignments</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{formatPercent(payload.summary.average_progress)}</div>
          <div className="stat-label">Average Progress</div>
        </div>
      </section>

      {alerts.length === 0 ? (
        <div className="alert-empty">
          <h2>Everything is on track</h2>
          <p>There are no current alerts for this account.</p>
        </div>
      ) : (
        <div className="alert-list">
          {alerts.map((alert) => (
            <article key={`${alert.course_id}-${alert.student_id}`} className={`card alert-card priority-${alert.priority}`}>
              <div className="card-body">
                <div className="alert-header">
                  <div>
                    <h3>{alert.course_title}</h3>
                    <p className="card-meta">
                      {payload.scope === 'student' ? `Instructor: ${alert.instructor_name}` : `Learner: ${alert.student_name}`}
                      {' '}
                      • {alert.course_category}
                    </p>
                  </div>
                  <div>
                    <div className="alert-score">{Math.round(alert.risk_score * 100)}%</div>
                    <div className="alert-score-label">Risk score</div>
                  </div>
                </div>

                <div className="alert-card-meta">
                  <span className={`badge ${priorityBadge(alert.priority)}`}>{priorityLabel(alert.priority)}</span>
                  <span className="alert-detail">{alert.progress_percent}% complete</span>
                  <span className="alert-detail">{alert.submitted_assignments} submitted</span>
                  <span className="alert-detail">{alert.graded_assignments} graded</span>
                </div>

                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${alert.progress_percent}%` }} />
                </div>

                <div className="alert-grid">
                  <div className="alert-stat">
                    <div className="alert-stat-label">Progress</div>
                    <div className="alert-stat-value">{formatPercent(alert.progress_percent)}</div>
                  </div>
                  <div className="alert-stat">
                    <div className="alert-stat-label">Assignments</div>
                    <div className="alert-stat-value">{alert.overdue_assignments} overdue</div>
                  </div>
                  <div className="alert-stat">
                    <div className="alert-stat-label">Quiz average</div>
                    <div className="alert-stat-value">{alert.best_quiz_score === null || alert.best_quiz_score === undefined ? 'No attempts' : formatPercent(alert.best_quiz_score)}</div>
                  </div>
                  <div className="alert-stat">
                    <div className="alert-stat-label">Assignment average</div>
                    <div className="alert-stat-value">{alert.average_grade === null || alert.average_grade === undefined ? 'No grades' : formatPercent(alert.average_grade)}</div>
                  </div>
                </div>

                <div className="alert-section">
                  <h4>Why this is showing</h4>
                  <ul className="alert-list-bullets">
                    {alert.reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </div>

                <div className="alert-section">
                  <h4>Suggested next steps</h4>
                  <ul className="alert-list-bullets">
                    {alert.next_steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ul>
                </div>

                {alert.due_items.length > 0 && (
                  <div className="alert-section">
                    <h4>Pending items</h4>
                    <div className="alert-due-list">
                      {alert.due_items.map((item) => (
                        <div key={item.assignment_id} className="alert-due-item">
                          <span>{item.title}</span>
                          <span>{formatDate(item.due_date)} • {item.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="alert-actions">
                  <a href={`/courses/${alert.course_id}`} className="btn-primary">Open course</a>
                  <a href="/assignments" className="btn-secondary">View assignments</a>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}