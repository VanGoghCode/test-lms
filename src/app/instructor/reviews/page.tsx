'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../auth-context'

type QueueStatus = 'pending' | 'approved' | 'rejected'

interface ModerationItem {
  id: number
  course_id: number
  course_title: string
  user_id: number
  user_name: string
  user_avatar: string
  rating: number
  content: string
  status: QueueStatus
  created_at: string
  moderated_at?: string
  moderator_name?: string
  moderation_note?: string
}

interface QueueResponse {
  items: ModerationItem[]
  detail?: string
}

function renderStars(rating: number): string {
  return `${'★'.repeat(rating)}${'☆'.repeat(5 - rating)}`
}

export default function ReviewModerationPage() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()

  const [statusFilter, setStatusFilter] = useState<QueueStatus>('pending')
  const [items, setItems] = useState<ModerationItem[]>([])
  const [notes, setNotes] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [savingReviewId, setSavingReviewId] = useState<number | null>(null)
  const [error, setError] = useState('')

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
    setLoading(true)
    setError('')

    fetch(`${baseUrl}/api/reviews/moderation-queue?status=${statusFilter}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        const data = await response.json() as QueueResponse
        if (!response.ok) {
          throw new Error(data.detail || 'Failed to load moderation queue')
        }
        setItems(data.items || [])
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [authLoading, router, statusFilter, token, user])

  const handleModeration = async (reviewId: number, nextStatus: Exclude<QueueStatus, 'pending'>) => {
    if (!token) {
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const moderationNote = notes[reviewId]?.trim()
    setSavingReviewId(reviewId)
    setError('')

    try {
      const response = await fetch(`${baseUrl}/api/reviews/${reviewId}/moderate`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: nextStatus,
          moderation_note: moderationNote || undefined,
        }),
      })

      const data = await response.json() as { detail?: string }
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update review status')
      }

      setItems((previous) => previous.filter((item) => item.id !== reviewId))
      setNotes((previous) => ({ ...previous, [reviewId]: '' }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update review status')
    } finally {
      setSavingReviewId(null)
    }
  }

  if (authLoading || loading) {
    return <p>Loading review moderation queue...</p>
  }

  return (
    <div className="moderation-page">
      <div className="page-header">
        <h1>Review Moderation</h1>
        <div style={{ display: 'flex', gap: 12 }}>
          <a href="/instructor" className="btn-secondary">Back to Instructor</a>
        </div>
      </div>

      <p className="subtitle">Approve or reject learner course reviews before they appear on course pages.</p>

      <div className="moderation-filters">
        <button
          type="button"
          className={`filter-btn ${statusFilter === 'pending' ? 'active' : ''}`}
          onClick={() => setStatusFilter('pending')}
        >
          Pending
        </button>
        <button
          type="button"
          className={`filter-btn ${statusFilter === 'approved' ? 'active' : ''}`}
          onClick={() => setStatusFilter('approved')}
        >
          Approved
        </button>
        <button
          type="button"
          className={`filter-btn ${statusFilter === 'rejected' ? 'active' : ''}`}
          onClick={() => setStatusFilter('rejected')}
        >
          Rejected
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {items.length === 0 ? (
        <p className="empty-state">No reviews found for this status.</p>
      ) : (
        <div className="moderation-list">
          {items.map((item) => (
            <article key={item.id} className="moderation-card">
              <div className="moderation-top-row">
                <div>
                  <h3>{item.course_title}</h3>
                  <p className="card-meta">Learner: {item.user_name}</p>
                </div>
                <div className="moderation-rating">{renderStars(item.rating)}</div>
              </div>

              <p>{item.content}</p>
              <p className="card-meta">Submitted on {new Date(item.created_at).toLocaleString()}</p>

              {statusFilter === 'pending' ? (
                <>
                  <div className="form-group" style={{ marginTop: 14 }}>
                    <label htmlFor={`note-${item.id}`}>Moderator note (optional)</label>
                    <textarea
                      id={`note-${item.id}`}
                      rows={3}
                      placeholder="Add context for the moderation decision"
                      value={notes[item.id] || ''}
                      onChange={(event) => {
                        const value = event.target.value
                        setNotes((previous) => ({ ...previous, [item.id]: value }))
                      }}
                    />
                  </div>

                  <div className="moderation-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      disabled={savingReviewId === item.id}
                      onClick={() => handleModeration(item.id, 'approved')}
                    >
                      {savingReviewId === item.id ? 'Saving...' : 'Approve'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={savingReviewId === item.id}
                      onClick={() => handleModeration(item.id, 'rejected')}
                    >
                      Reject
                    </button>
                  </div>
                </>
              ) : (
                <div className="moderation-history">
                  <p className="card-meta">
                    Moderated by {item.moderator_name || 'Unknown'} on {item.moderated_at ? new Date(item.moderated_at).toLocaleString() : 'N/A'}
                  </p>
                  {item.moderation_note && <p className="card-meta">Note: {item.moderation_note}</p>}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
