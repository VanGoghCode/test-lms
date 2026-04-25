'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../auth-context'

interface EngagementPoint {
  day: string
  value: number
}

interface RevenuePoint {
  month: string
  value: number
}

interface CourseMetric {
  course_id: number
  course_title: string
  views: number
  enrollments: number
  completions: number
  completion_rate: number
  avg_progress: number
  revenue: number
}

interface AnalyticsPayload {
  summary: {
    total_views: number
    total_enrollments: number
    total_completions: number
    course_count: number
  }
  engagement: {
    avg_progress: number
    active_learners: number
    completion_rate: number
    weekly_engagement: EngagementPoint[]
  }
  earnings: {
    total_revenue: number
    avg_order_value: number
    monthly_revenue: RevenuePoint[]
  }
  courses: CourseMetric[]
}

function Currency({ value }: { value: number }) {
  return <>{new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)}</>
}

export default function InstructorAnalyticsPage() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null)

  useEffect(() => {
    if (authLoading) {
      return
    }

    if (!user || !token) {
      router.push('/login')
      return
    }

    if (user.role !== 'instructor' && user.role !== 'admin') {
      router.push('/')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/instructor/analytics`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || 'Failed to load analytics')
        }
        setAnalytics(data)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authLoading, router, token, user])

  const chartValues = useMemo(() => {
    if (!analytics) {
      return {
        weeklyMax: 1,
        monthlyMax: 1,
      }
    }

    const weeklyMax = Math.max(...analytics.engagement.weekly_engagement.map((d) => d.value), 1)
    const monthlyMax = Math.max(...analytics.earnings.monthly_revenue.map((d) => d.value), 1)
    return { weeklyMax, monthlyMax }
  }, [analytics])

  if (authLoading || loading) {
    return <p>Loading analytics...</p>
  }

  if (error) {
    return <p className="error-message">{error}</p>
  }

  if (!analytics) {
    return <p className="subtitle">No analytics available.</p>
  }

  return (
    <>
      <div className="page-header">
        <h1>Analytics Dashboard</h1>
        <a href="/instructor" className="btn-secondary">Back to Instructor</a>
      </div>
      <p className="subtitle">Track views, enrollments, completions, engagement, and earnings for your courses.</p>

      <section className="stats">
        <div className="stat-card">
          <div className="stat-value">{analytics.summary.total_views}</div>
          <div className="stat-label">Course Views</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analytics.summary.total_enrollments}</div>
          <div className="stat-label">Enrollments</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analytics.summary.total_completions}</div>
          <div className="stat-label">Completions</div>
        </div>
        <div className="stat-card">
          <div className="stat-value"><Currency value={analytics.earnings.total_revenue} /></div>
          <div className="stat-label">Instructor Earnings</div>
        </div>
      </section>

      <section className="analytics-grid">
        <article className="card analytics-card">
          <div className="card-body">
            <h3 className="card-title">Weekly Engagement</h3>
            <p className="card-meta">Learner activity by enrollment day</p>
            <div className="bar-chart">
              {analytics.engagement.weekly_engagement.map((point) => (
                <div key={point.day} className="bar-group">
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ height: `${Math.max((point.value / chartValues.weeklyMax) * 100, 6)}%` }}
                    />
                  </div>
                  <span className="bar-label">{point.day}</span>
                  <span className="bar-value">{point.value}</span>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="card analytics-card">
          <div className="card-body">
            <h3 className="card-title">Monthly Revenue</h3>
            <p className="card-meta">Estimated earnings trend</p>
            <svg viewBox="0 0 360 180" className="line-chart" role="img" aria-label="Monthly revenue line chart">
              <polyline
                fill="none"
                stroke="var(--primary)"
                strokeWidth="3"
                points={analytics.earnings.monthly_revenue
                  .map((point, idx) => {
                    const x = 30 + idx * 100
                    const y = 160 - (point.value / chartValues.monthlyMax) * 120
                    return `${x},${y}`
                  })
                  .join(' ')}
              />
              {analytics.earnings.monthly_revenue.map((point, idx) => {
                const x = 30 + idx * 100
                const y = 160 - (point.value / chartValues.monthlyMax) * 120
                return (
                  <g key={point.month}>
                    <circle cx={x} cy={y} r="4" fill="var(--primary)" />
                    <text x={x} y="174" textAnchor="middle" className="line-chart-label">{point.month}</text>
                  </g>
                )
              })}
            </svg>
            <p className="card-meta">
              Average Order Value: <strong><Currency value={analytics.earnings.avg_order_value} /></strong>
            </p>
          </div>
        </article>
      </section>

      <section>
        <h2>Student Engagement Metrics</h2>
        <div className="stats">
          <div className="stat-card">
            <div className="stat-value">{analytics.engagement.avg_progress}%</div>
            <div className="stat-label">Average Progress</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{analytics.engagement.active_learners}</div>
            <div className="stat-label">Active Learners</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{analytics.engagement.completion_rate}%</div>
            <div className="stat-label">Completion Rate</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{analytics.summary.course_count}</div>
            <div className="stat-label">Total Courses</div>
          </div>
        </div>
      </section>

      <section>
        <h2>Course Performance</h2>
        <div className="table-wrap">
          <table className="analytics-table">
            <thead>
              <tr>
                <th>Course</th>
                <th>Views</th>
                <th>Enrollments</th>
                <th>Completions</th>
                <th>Completion Rate</th>
                <th>Avg Progress</th>
                <th>Earnings</th>
              </tr>
            </thead>
            <tbody>
              {analytics.courses.map((course) => (
                <tr key={course.course_id}>
                  <td>{course.course_title}</td>
                  <td>{course.views}</td>
                  <td>{course.enrollments}</td>
                  <td>{course.completions}</td>
                  <td>{course.completion_rate}%</td>
                  <td>{course.avg_progress}%</td>
                  <td><Currency value={course.revenue} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}
