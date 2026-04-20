'use client'

import { FormEvent, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '../../auth-context'

interface Course {
  id: number
  title: string
  description: string
  instructor: { id: number; name: string; avatar: string }
  category: string
  level: 'beginner' | 'intermediate' | 'advanced'
  thumbnail: string
  duration: string
  average_rating: number
  rating_count: number
  modules: { id: number; title: string; lessons: { id: number; title: string; duration: string; video_url?: string }[] }[]
}

interface CourseReview {
  id: number
  course_id: number
  user_id: number
  user_name: string
  user_avatar: string
  rating: number
  content: string
  created_at: string
}

interface ReviewsPayload {
  summary: {
    average_rating: number
    rating_count: number
  }
  distribution: Record<string, number>
  reviews: CourseReview[]
}

interface Progress {
  course_id: number
  completed_lessons: number[]
  total_lessons: number
  progress_percent: number
}

interface CompletionStatus {
  can_generate: boolean
  has_certificate: boolean
  message: string
}

export default function CourseDetail() {
  const params = useParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [course, setCourse] = useState<Course | null>(null)
  const [reviews, setReviews] = useState<CourseReview[]>([])
  const [ratingSummary, setRatingSummary] = useState({ average_rating: 0, rating_count: 0 })
  const [ratingDistribution, setRatingDistribution] = useState<Record<string, number>>({
    '1': 0,
    '2': 0,
    '3': 0,
    '4': 0,
    '5': 0,
  })
  const [reviewRating, setReviewRating] = useState(5)
  const [reviewContent, setReviewContent] = useState('')
  const [reviewMessage, setReviewMessage] = useState('')
  const [reviewError, setReviewError] = useState('')
  const [reviewSubmitting, setReviewSubmitting] = useState(false)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [enrolled, setEnrolled] = useState(false)
  const [completionStatus, setCompletionStatus] = useState<CompletionStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [inWishlist, setInWishlist] = useState(false)

  const loadReviews = async (baseUrl: string) => {
    const response = await fetch(`${baseUrl}/api/courses/${params.id}/reviews`)
    const data = await response.json() as ReviewsPayload
    if (!response.ok) {
      throw new Error('Failed to load course reviews')
    }
    setReviews(data.reviews || [])
    setRatingSummary(data.summary || { average_rating: 0, rating_count: 0 })
    setRatingDistribution({
      '1': 0,
      '2': 0,
      '3': 0,
      '4': 0,
      '5': 0,
      ...(data.distribution || {}),
    })
  }

  useEffect(() => {
    if (authLoading) return

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    fetch(`${baseUrl}/api/courses/${params.id}`)
      .then(r => r.json())
      .then(setCourse)

    loadReviews(baseUrl).catch(() => {
      setReviews([])
      setRatingSummary({ average_rating: 0, rating_count: 0 })
    })

    if (user && token) {
      fetch(`${baseUrl}/api/users/${user.id}/enrollments`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(enrollments => {
          const found = enrollments.find((e: any) => e.course_id === Number(params.id))
          setEnrolled(!!found)
        })

      fetch(`${baseUrl}/api/courses/${params.id}/progress`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(setProgress)
        .catch(() => setProgress(null))

      fetch(`${baseUrl}/api/courses/${params.id}/completion-status`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(setCompletionStatus)
        .catch(() => setCompletionStatus(null))
        .finally(() => setLoading(false))

      fetch(`${baseUrl}/api/wishlist/check/${params.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(data => setInWishlist(data.in_wishlist))
        .catch(() => setInWishlist(false))
    } else {
      setLoading(false)
    }
  }, [params.id, user, token, authLoading])

  const handleReviewSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setReviewMessage('')
    setReviewError('')

    if (!user || !token) {
      router.push('/login')
      return
    }

    if (user.role !== 'student') {
      setReviewError('Only students can submit course reviews.')
      return
    }

    if (reviewContent.trim().length < 10) {
      setReviewError('Please write at least 10 characters for your review.')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    setReviewSubmitting(true)
    try {
      const response = await fetch(`${baseUrl}/api/courses/${params.id}/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          rating: reviewRating,
          content: reviewContent.trim(),
        }),
      })

      const data = await response.json() as { detail?: string }
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to submit review')
      }

      setReviewContent('')
      setReviewMessage('Thanks! Your review is submitted and pending moderation.')
      await loadReviews(baseUrl)
    } catch (error) {
      setReviewError(error instanceof Error ? error.message : 'Unable to submit review')
    } finally {
      setReviewSubmitting(false)
    }
  }

  const handleEnroll = async () => {
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    await fetch(`${baseUrl}/api/courses/${params.id}/enroll?user_id=${user.id}`, { 
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    setEnrolled(true)
    // Fetch fresh progress
    const res = await fetch(`${baseUrl}/api/courses/${params.id}/progress`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    setProgress(await res.json())
  }

  const toggleLessonComplete = async (lessonId: number) => {
    if (!user || !token) return

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const isCompleted = progress?.completed_lessons.includes(lessonId)
    
    await fetch(`${baseUrl}/api/courses/${params.id}/progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ lesson_id: lessonId, completed: !isCompleted })
    })

    // Refresh progress and completion status
    const res = await fetch(`${baseUrl}/api/courses/${params.id}/progress`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    setProgress(await res.json())

    const statusRes = await fetch(`${baseUrl}/api/courses/${params.id}/completion-status`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    setCompletionStatus(await statusRes.json())
  }

  const handleGenerateCertificate = async () => {
    if (!user || !token) return

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    try {
      const res = await fetch(`${baseUrl}/api/courses/${params.id}/certificate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (!res.ok) {
        const error = await res.json()
        alert(error.detail)
        return
      }

      const cert = await res.json()
      router.push(`/certificates/${cert.verification_code}`)
    } catch (err) {
      console.error(err)
      alert('Failed to generate certificate')
    }
  }

  const toggleWishlist = async () => {
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    try {
      if (inWishlist) {
        await fetch(`${baseUrl}/api/wishlist/${params.id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        })
        setInWishlist(false)
      } else {
        await fetch(`${baseUrl}/api/wishlist/${params.id}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        })
        setInWishlist(true)
      }
    } catch (err) {
      console.error('Failed to update wishlist:', err)
    }
  }

  if (authLoading || loading || !course) return <div className="container"><p>Loading...</p></div>

  return (
    <div className="course-detail">
      <div className="course-main">
        <h1>{course.title}</h1>
        <div className="course-meta">
          <span>👤 {course.instructor.name}</span>
          <span>⏱️ {course.duration}</span>
          <span>📚 {course.category}</span>
          <span>⭐ {ratingSummary.average_rating.toFixed(1)} ({ratingSummary.rating_count} review{ratingSummary.rating_count === 1 ? '' : 's'})</span>
        </div>
        <p className="course-description">{course.description}</p>

        <div className="course-tabs">
          <a href={`/courses/${params.id}/discussions`} className="tab-link">💬 Discussions</a>
        </div>

        {enrolled && progress && (
          <>
            <h2>Your Progress</h2>
            <div className="progress-overview">
              <div className="progress-bar large">
                <div className="progress-fill" style={{ width: `${progress.progress_percent}%` }} />
              </div>
              <span className="progress-text">{progress.progress_percent}% complete ({progress.completed_lessons.length}/{progress.total_lessons} lessons)</span>
            </div>
          </>
        )}

        <section className="reviews-panel">
          <div className="reviews-heading-row">
            <h2>Course Reviews</h2>
            <p className="review-summary-inline">
              {ratingSummary.average_rating.toFixed(1)} / 5 from {ratingSummary.rating_count} learner{ratingSummary.rating_count === 1 ? '' : 's'}
            </p>
          </div>

          <div className="rating-breakdown" aria-label="Rating breakdown">
            {[5, 4, 3, 2, 1].map((star) => {
              const count = ratingDistribution[String(star)] || 0
              const width = ratingSummary.rating_count > 0 ? (count / ratingSummary.rating_count) * 100 : 0
              return (
                <div key={star} className="rating-row">
                  <span>{star}★</span>
                  <div className="rating-row-track">
                    <div className="rating-row-fill" style={{ width: `${width}%` }} />
                  </div>
                  <span>{count}</span>
                </div>
              )
            })}
          </div>

          {reviews.length === 0 ? (
            <p className="subtitle" style={{ marginBottom: 16 }}>No approved reviews yet.</p>
          ) : (
            <div className="review-list">
              {reviews.map((review) => (
                <article key={review.id} className="review-card">
                  <div className="review-card-top">
                    <div className="author">
                      <span className="avatar-small">{review.user_avatar}</span>
                      <strong>{review.user_name}</strong>
                    </div>
                    <span className="review-stars">{'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}</span>
                  </div>
                  <p>{review.content}</p>
                  <p className="card-meta">Posted on {new Date(review.created_at).toLocaleDateString()}</p>
                </article>
              ))}
            </div>
          )}

          {user?.role === 'student' && (
            <form className="review-form" onSubmit={handleReviewSubmit}>
              <h3>Write a Review</h3>

              {reviewError && <div className="error-message">{reviewError}</div>}
              {reviewMessage && <p className="success-message">{reviewMessage}</p>}

              <div className="form-group">
                <label htmlFor="review-rating">Your rating</label>
                <select
                  id="review-rating"
                  value={reviewRating}
                  onChange={(event) => setReviewRating(Number(event.target.value))}
                >
                  <option value={5}>5 - Excellent</option>
                  <option value={4}>4 - Good</option>
                  <option value={3}>3 - Average</option>
                  <option value={2}>2 - Fair</option>
                  <option value={1}>1 - Poor</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="review-content">Your feedback</label>
                <textarea
                  id="review-content"
                  rows={4}
                  maxLength={2000}
                  value={reviewContent}
                  onChange={(event) => setReviewContent(event.target.value)}
                  placeholder="Share what worked well and what could improve."
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={reviewSubmitting}>
                {reviewSubmitting ? 'Submitting...' : 'Submit Review'}
              </button>
            </form>
          )}
        </section>

        <h2>Course Content</h2>
        {course.modules.map(module => (
          <div key={module.id} className="module">
            <div className="module-header">{module.title}</div>
            {module.lessons.map(lesson => {
              const isCompleted = progress?.completed_lessons.includes(lesson.id)
              return (
                <div 
                  key={lesson.id} 
                  className={`lesson ${enrolled ? 'clickable' : ''}`}
                  onClick={() => enrolled && toggleLessonComplete(lesson.id)}
                >
                  <div className="lesson-left">
                    {enrolled && (
                      <span className={`lesson-check ${isCompleted ? 'completed' : ''}`}>
                        {isCompleted ? '✓' : '○'}
                      </span>
                    )}
                    <span className={isCompleted ? 'lesson-completed' : ''}>{lesson.title}</span>
                  </div>
                  <div className="lesson-right">
                    {lesson.video_url && <span className="video-icon">🎥</span>}
                    <span>{lesson.duration}</span>
                  </div>
                </div>
              )
            })}
          </div>
        ))}
      </div>
      <div className="course-sidebar">
        <div className="enroll-card">
          {enrolled ? (
            <>
              <p>Your Progress</p>
              <div className="progress-bar" style={{ marginTop: 12 }}>
                <div className="progress-fill" style={{ width: `${progress?.progress_percent || 0}%` }} />
              </div>
              <p style={{ marginTop: 8, color: 'var(--text-secondary)' }}>{progress?.progress_percent || 0}% complete</p>
              <button className="btn btn-primary" style={{ marginTop: 16 }}>Continue Learning</button>
              
              {completionStatus?.has_certificate && (
                <a href="/certificates" className="btn btn-secondary" style={{ marginTop: 12, display: 'block', textAlign: 'center' }}>
                  View Certificate
                </a>
              )}
              
              {completionStatus?.can_generate && (
                <button onClick={handleGenerateCertificate} className="btn btn-primary" style={{ marginTop: 12, background: 'var(--success)' }}>
                  🏆 Generate Certificate
                </button>
              )}
              
              {!completionStatus?.can_generate && !completionStatus?.has_certificate && (
                <p style={{ marginTop: 12, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  {completionStatus?.message}
                </p>
              )}
            </>
          ) : (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>Not enrolled yet</p>
              <button className="btn btn-primary" onClick={handleEnroll}>Enroll Now</button>
              <button 
                className="btn btn-secondary" 
                style={{ marginTop: 12 }}
                onClick={toggleWishlist}
              >
                {inWishlist ? '❤️ Remove from Wishlist' : '🤍 Add to Wishlist'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}