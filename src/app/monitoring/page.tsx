'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../auth-context'

interface MonitoringLearner {
  learner_id: number
  learner_name: string
  course_id: number
  course_name: string
  course_code: string
  attendance_percentage: number
  completion_percentage: number
  risk_score: number
  risk_label: string
  status: string
  overall_status: string
}

interface MonitoringResponse {
  generated_at: string
  summary: {
    learners: number
    at_risk: number
    follow_up: number
    below_attendance_target: number
    below_completion_target: number
  }
  learners: MonitoringLearner[]
  notifications: {
    total: number
    queued: number
    delivered: number
    latest_status: string
  }
}

interface AnalyticsResponse {
  generated_at: string
  summary_text: string
  buckets: { label: string; count: number }[]
  categories: { label: string; count: number }[]
}

interface NotificationItem {
  id: number
  learner_name: string
  course_name: string
  status: string
  score: number
  channel_status: string
  created_at: string
}

function statusLabel(value: string) {
  if (value === 'high concern') return 'badge-error'
  if (value === 'warning') return 'badge-warning'
  return 'badge-success'
}

function formatPercent(value: number) {
  return `${Math.round(value)}%`
}

export default function MonitoringPage() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [payload, setPayload] = useState<MonitoringResponse | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')

  useEffect(() => {
    if (authLoading) return

    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    Promise.all([
      fetch(`${baseUrl}/api/monitoring/learners`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${baseUrl}/api/monitoring/analytics`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${baseUrl}/api/notifications`, { headers: { Authorization: `Bearer ${token}` } }),
    ])
      .then(async ([learnersRes, analyticsRes, notificationsRes]) => {
        const learnersData = await learnersRes.json()
        const analyticsData = await analyticsRes.json()
        const notificationsData = await notificationsRes.json()
        if (!learnersRes.ok) throw new Error(learnersData.detail || 'Failed to load monitoring data')
        if (!analyticsRes.ok) throw new Error(analyticsData.detail || 'Failed to load analytics data')
        if (!notificationsRes.ok) throw new Error(notificationsData.detail || 'Failed to load notifications')
        setPayload(learnersData)
        setAnalytics(analyticsData)
        setNotifications(notificationsData.items || [])
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authLoading, router, token, user])

  const visibleLearners = useMemo(() => {
    if (!payload) return []
    return payload.learners.filter((item) => {
      const matchesSearch = !search || [item.learner_name, item.course_name, item.status].join(' ').toLowerCase().includes(search.toLowerCase())
      const matchesStatus = status === 'all' || item.status === status
      return matchesSearch && matchesStatus
    })
  }, [payload, search, status])

  if (authLoading || loading) {
    return <p>Loading monitoring...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  if (!payload || !analytics) {
    return <p className="subtitle">No monitoring data available.</p>
  }

  return (
    <div className="monitoring-page">
      <div className="page-header monitoring-header">
        <div>
          <h1>Learner Monitoring</h1>
          <p className="subtitle">Current attendance, completion, and risk snapshots across the selected scope.</p>
          <div className="alerts-meta">
            <span className="alert-chip">Updated {payload.generated_at}</span>
            <span className="alert-chip">{payload.summary.at_risk} at risk</span>
            <span className="alert-chip">{payload.notifications.queued} queued alerts</span>
          </div>
        </div>
        <div className="monitoring-actions">
          <a href="/alerts" className="btn-secondary">Learning Alerts</a>
          <a href="/my-learning" className="btn-secondary">My Learning</a>
        </div>
      </div>

      <section className="stats">
        <div className="stat-card">
          <div className="stat-value">{payload.summary.learners}</div>
          <div className="stat-label">Learners</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{payload.summary.at_risk}</div>
          <div className="stat-label">At Risk</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{payload.summary.follow_up}</div>
          <div className="stat-label">Follow-up</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{payload.notifications.delivered}</div>
          <div className="stat-label">Delivered Notifications</div>
        </div>
      </section>

      <section className="monitoring-toolbar card">
        <div className="card-body monitoring-toolbar-inner">
          <input
            className="monitoring-input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search learner, course, or status"
          />
          <select className="monitoring-select" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="all">All statuses</option>
            <option value="safe">Safe</option>
            <option value="warning">Warning</option>
            <option value="high concern">High concern</option>
          </select>
        </div>
      </section>

      <section className="monitoring-grid">
        {visibleLearners.map((learner) => (
          <article key={`${learner.learner_id}-${learner.course_id}`} className="card monitoring-card">
            <div className="card-body">
              <div className="monitoring-card-top">
                <div>
                  <div className={`badge ${statusLabel(learner.status)}`}>{learner.status}</div>
                  <h3>{learner.learner_name}</h3>
                  <p className="card-meta">{learner.course_name || learner.course_code}</p>
                </div>
                <div className="monitoring-score">
                  <div className="monitoring-score-value">{learner.risk_score.toFixed(2)}</div>
                  <div className="monitoring-score-label">Risk score</div>
                </div>
              </div>

              <div className="monitoring-status-row">
                <span className={`badge ${statusLabel(learner.overall_status)}`}>{learner.overall_status}</span>
                <span className="monitoring-inline">{learner.risk_label}</span>
              </div>

              <div className="monitoring-metrics">
                <div className="monitoring-metric">
                  <span>Attendance</span>
                  <strong>{formatPercent(learner.attendance_percentage)}</strong>
                </div>
                <div className="monitoring-metric">
                  <span>Completion</span>
                  <strong>{formatPercent(learner.completion_percentage)}</strong>
                </div>
                <div className="monitoring-metric">
                  <span>Status</span>
                  <strong>{learner.status}</strong>
                </div>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="monitoring-panel-grid">
        <article className="card">
          <div className="card-body">
            <h2>Concern Categories</h2>
            <p className="card-meta">{analytics.summary_text}</p>
            <div className="monitoring-bars">
              {analytics.categories.map((bucket) => (
                <div key={bucket.label} className="monitoring-bar-row">
                  <div className="monitoring-bar-label">{bucket.label}</div>
                  <div className="monitoring-bar-track">
                    <div className="monitoring-bar-fill" style={{ width: `${Math.max(bucket.count * 20, 8)}%` }} />
                  </div>
                  <div className="monitoring-bar-count">{bucket.count}</div>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="card">
          <div className="card-body">
            <h2>Notification Queue</h2>
            <p className="card-meta">Newest items appear first.</p>
            <div className="notification-list">
              {notifications.slice(0, 6).map((item) => (
                <div key={item.id} className="notification-item">
                  <div>
                    <strong>{item.learner_name || 'Learner'}</strong>
                    <p>{item.course_name || 'Course'}</p>
                  </div>
                  <div>
                    <span className={`badge ${item.channel_status === 'queued' ? 'badge-warning' : 'badge-success'}`}>{item.channel_status}</span>
                    <p className="notification-score">{item.status} · {item.score.toFixed(2)}</p>
                  </div>
                </div>
              ))}
              {notifications.length === 0 && <p className="subtitle">No notifications yet.</p>}
            </div>
          </div>
        </article>
      </section>
    </div>
  )
}