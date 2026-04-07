'use client'
import { useAuth } from '../../auth-context'
import { useRouter } from 'next/navigation'
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
  user_name: string
  content: string
  file_url?: string
  submitted_at: string
  is_late: boolean
  grade?: number
  feedback?: string
}

export default function InstructorAssignments() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const [grading, setGrading] = useState<number | null>(null)
  const [grade, setGrade] = useState('')
  const [feedback, setFeedback] = useState('')

  useEffect(() => {
    if (authLoading) return
    
    if (!user || !token) {
      router.push('/login')
      return
    }

    if (user.role !== 'instructor' && user.role !== 'admin') {
      router.push('/')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/instructor/assignments`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setAssignments)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user, token, authLoading, router])

  const loadSubmissions = (assignment: Assignment) => {
    setSelectedAssignment(assignment)
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/assignments/${assignment.id}/submissions`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setSubmissions)
      .catch(console.error)
  }

  const handleGrade = async (userId: number) => {
    setGrading(userId)
  }

  const submitGrade = async (userId: number) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    const res = await fetch(`${baseUrl}/api/assignments/${selectedAssignment?.id}/grade?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        grade: parseInt(grade),
        feedback: feedback || null
      })
    })

    if (res.ok) {
      const data = await res.json()
      alert(`Graded! Original: ${data.original_grade}, Final: ${data.grade}${data.late_penalty_applied ? ' (10% late penalty applied)' : ''}`)
      setGrading(null)
      setGrade('')
      setFeedback('')
      loadSubmissions(selectedAssignment!)
    }
  }

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <>
      <h1>Assignment Management</h1>
      <p className="subtitle">Grade and manage student submissions</p>

      <div className="instructor-assignments">
        <div className="assignments-list">
          <h2>My Assignments</h2>
          {assignments.map(assignment => (
            <div 
              key={assignment.id} 
              className={`assignment-card ${selectedAssignment?.id === assignment.id ? 'selected' : ''}`}
              onClick={() => loadSubmissions(assignment)}
            >
              <h3>{assignment.title}</h3>
              <p>{assignment.course_name}</p>
              <p className="due">Due: {assignment.due_date}</p>
              <span className={`badge badge-${assignment.status === 'graded' ? 'success' : assignment.status === 'submitted' ? 'warning' : 'error'}`}>
                {assignment.status}
              </span>
            </div>
          ))}
        </div>

        <div className="submissions-panel">
          {selectedAssignment ? (
            <>
              <h2>Submissions: {selectedAssignment.title}</h2>
              {submissions.length === 0 ? (
                <p className="empty-state">No submissions yet</p>
              ) : (
                submissions.map(sub => (
                  <div key={sub.user_id} className="submission-card">
                    <div className="submission-header">
                      <h3>{sub.user_name}</h3>
                      {sub.is_late && <span className="late-badge">Late</span>}
                    </div>
                    <p className="submitted-at">Submitted: {sub.submitted_at}</p>
                    <div className="submission-content">
                      <h4>Answer:</h4>
                      <p>{sub.content}</p>
                    </div>
                    {sub.file_url && (
                      <p className="file-link">File: <a href={sub.file_url} target="_blank" rel="noopener">View Attachment</a></p>
                    )}
                    
                    {grading === sub.user_id ? (
                      <div className="grading-form">
                        <div className="form-group">
                          <label>Grade (out of {selectedAssignment.max_grade})</label>
                          <input
                            type="number"
                            value={grade}
                            onChange={e => setGrade(e.target.value)}
                            min="0"
                            max={selectedAssignment.max_grade}
                          />
                        </div>
                        <div className="form-group">
                          <label>Feedback</label>
                          <textarea
                            value={feedback}
                            onChange={e => setFeedback(e.target.value)}
                            rows={3}
                            placeholder="Provide feedback..."
                          />
                        </div>
                        <div className="form-actions">
                          <button onClick={() => setGrading(null)} className="btn-secondary">Cancel</button>
                          <button onClick={() => submitGrade(sub.user_id)} className="btn-primary">Submit Grade</button>
                        </div>
                      </div>
                    ) : (
                      <div className="submission-actions">
                        {sub.grade !== undefined ? (
                          <div className="grade-display">
                            <span className="grade">Grade: {sub.grade}/{selectedAssignment.max_grade}</span>
                            {sub.feedback && <p className="feedback">Feedback: {sub.feedback}</p>}
                          </div>
                        ) : (
                          <button onClick={() => handleGrade(sub.user_id)} className="btn-primary">Grade</button>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </>
          ) : (
            <p className="empty-state">Select an assignment to view submissions</p>
          )}
        </div>
      </div>
    </>
  )
}