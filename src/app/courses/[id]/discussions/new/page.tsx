'use client'
import { useAuth } from '../../../../auth-context'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function NewDiscussion() {
  const params = useParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (authLoading) return
    if (!user || !token) {
      router.push('/login')
    }
  }, [user, token, authLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(`${baseUrl}/api/discussions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          course_id: Number(params.id),
          title,
          content
        })
      })

      if (!res.ok) throw new Error('Failed to create discussion')

      router.push(`/courses/${params.id}/discussions`)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading) return <div className="container"><p>Loading...</p></div>

  return (
    <div className="discussion-form-page">
      <h1>Start a Discussion</h1>
      <p className="subtitle">Ask questions or share insights with your classmates</p>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="discussion-form">
        <div className="form-group">
          <label>Title</label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
            placeholder="What's your question or topic?"
          />
        </div>

        <div className="form-group">
          <label>Content</label>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            required
            rows={10}
            placeholder="Provide details, context, or your thoughts..."
          />
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => router.back()} className="btn-secondary">Cancel</button>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? 'Posting...' : 'Post Discussion'}
          </button>
        </div>
      </form>
    </div>
  )
}