'use client'
import { useAuth } from '../../../auth-context'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Assignment {
  id: number
  title: string
  course_id: number
  course_name: string
  description: string
  due_date: string
  status: string
  max_grade: number
}

interface Submission {
  user_id: number
  content: string
  file_url?: string
  submitted_at: string
  is_late: boolean
  grade?: number
  feedback?: string
}

export default function SubmitAssignment() {
  const params = useParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [assignment, setAssignment] = useState<Assignment | null>(null)
  const [submission, setSubmission] = useState<Submission | null>(null)
  const [content, setContent] = useState('')
  const [fileUrl, setFileUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    fetch(`${baseUrl}/api/assignments/${params.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setAssignment)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [params.id, user, token, authLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setMessage('')

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    try {
      const res = await fetch(`${baseUrl}/api/assignments/${params.id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          assignment_id: Number(params.id),
          content,
          file_url: fileUrl || null
        })
      })

      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to submit')
      }

      setMessage(data.message)
      setSubmission(data)
      
      // Redirect after short delay
      setTimeout(() => router.push('/assignments'), 2000)
    } catch (err: any) {
      setMessage(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const isOverdue = assignment && new Date(assignment.due_date) < new Date()

  if (authLoading || loading || !assignment) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <div className="assignment-submit">
      <h1>{assignment.title}</h1>
      <p className="subtitle">{assignment.course_name}</p>

      <div className="assignment-details">
        <h3>Description</h3>
        <p>{assignment.description}</p>
        <p className="due-date">
          Due: {assignment.due_date}
          {isOverdue && <span className="overdue-badge"> - Overdue!</span>}
        </p>
        <p className="max-grade">Max Grade: {assignment.max_grade}</p>
      </div>

      {message && (
        <div className={`message ${message.includes('LATE') ? 'warning' : 'success'}`}>
          {message}
        </div>
      )}

      {submission ? (
        <div className="submission-status">
          <h3>Submission Received</h3>
          <p>Submitted at: {submission.submitted_at}</p>
          {submission.is_late && <p className="late-notice">Late submission - 10% penalty will apply</p>}
          {submission.grade !== undefined && (
            <p>Grade: {submission.grade}/{assignment.max_grade}</p>
          )}
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="submission-form">
          <div className="form-group">
            <label>Your Answer</label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              required
              rows={10}
              placeholder="Enter your answer here..."
            />
          </div>

          <div className="form-group">
            <label>File URL (optional)</label>
            <input
              type="url"
              value={fileUrl}
              onChange={e => setFileUrl(e.target.value)}
              placeholder="https://..."
            />
            <p className="form-hint">Upload your file to a cloud service and paste the URL here</p>
          </div>

          <div className="form-actions">
            <button type="button" onClick={() => router.back()} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit Assignment'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}