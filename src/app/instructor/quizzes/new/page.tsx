'use client'
import { useAuth } from '../../../auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Course {
  id: number
  title: string
}

interface Question {
  question: string
  type: 'multiple_choice' | 'true_false' | 'short_answer'
  options?: string[]
  correct_answer: string
  points: number
}

export default function NewQuiz() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [courses, setCourses] = useState<Course[]>([])
  const [title, setTitle] = useState('')
  const [courseId, setCourseId] = useState<number>(0)
  const [description, setDescription] = useState('')
  const [timeLimit, setTimeLimit] = useState('')
  const [passingScore, setPassingScore] = useState('70')
  const [questions, setQuestions] = useState<Question[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

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
    fetch(`${baseUrl}/api/instructor/courses`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => {
        setCourses(data)
        if (data.length > 0) setCourseId(data[0].id)
      })
      .catch(console.error)
  }, [user, token, authLoading, router])

  const addQuestion = () => {
    setQuestions([...questions, {
      question: '',
      type: 'multiple_choice',
      options: ['', '', '', ''],
      correct_answer: '',
      points: 1
    }])
  }

  const updateQuestion = (idx: number, field: string, value: any) => {
    const updated = [...questions]
    ;(updated[idx] as any)[field] = value
    setQuestions(updated)
  }

  const updateOption = (qIdx: number, optIdx: number, value: string) => {
    const updated = [...questions]
    if (updated[qIdx].options) {
      updated[qIdx].options![optIdx] = value
    }
    setQuestions(updated)
  }

  const removeQuestion = (idx: number) => {
    setQuestions(questions.filter((_, i) => i !== idx))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      // Create quiz
      const quizRes = await fetch(`${baseUrl}/api/quizzes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          title,
          course_id: courseId,
          description,
          time_limit: timeLimit ? parseInt(timeLimit) : null,
          passing_score: parseInt(passingScore)
        })
      })

      if (!quizRes.ok) throw new Error('Failed to create quiz')
      const quiz = await quizRes.json()

      // Add questions
      for (const q of questions) {
        if (!q.question) continue
        
        await fetch(`${baseUrl}/api/quizzes/${quiz.id}/questions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            question: q.question,
            type: q.type,
            options: q.type === 'multiple_choice' ? q.options?.filter(o => o) : null,
            correct_answer: q.correct_answer,
            points: q.points
          })
        })
      }

      router.push('/instructor/quizzes')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (authLoading) return <div className="container"><p>Loading...</p></div>

  return (
    <div className="quiz-editor">
      <h1>Create New Quiz</h1>
      <p className="subtitle">Build a quiz with auto-grading</p>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <h2>Quiz Details</h2>
          
          <div className="form-group">
            <label>Quiz Title</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
              placeholder="e.g., Python Basics Quiz"
            />
          </div>

          <div className="form-group">
            <label>Course</label>
            <select value={courseId} onChange={e => setCourseId(parseInt(e.target.value))}>
              {courses.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              required
              rows={3}
              placeholder="Describe the quiz..."
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Time Limit (minutes, optional)</label>
              <input
                type="number"
                value={timeLimit}
                onChange={e => setTimeLimit(e.target.value)}
                placeholder="e.g., 30"
              />
            </div>

            <div className="form-group">
              <label>Passing Score (%)</label>
              <input
                type="number"
                value={passingScore}
                onChange={e => setPassingScore(e.target.value)}
                min="0"
                max="100"
                required
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h2>Questions</h2>
          
          {questions.map((q, qIdx) => (
            <div key={qIdx} className="question-editor">
              <div className="question-header">
                <h3>Question {qIdx + 1}</h3>
                <button type="button" onClick={() => removeQuestion(qIdx)} className="btn-remove">×</button>
              </div>

              <div className="form-group">
                <label>Question Text</label>
                <input
                  type="text"
                  value={q.question}
                  onChange={e => updateQuestion(qIdx, 'question', e.target.value)}
                  placeholder="Enter your question..."
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Type</label>
                  <select value={q.type} onChange={e => updateQuestion(qIdx, 'type', e.target.value)}>
                    <option value="multiple_choice">Multiple Choice</option>
                    <option value="true_false">True/False</option>
                    <option value="short_answer">Short Answer</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Points</label>
                  <input
                    type="number"
                    value={q.points}
                    onChange={e => updateQuestion(qIdx, 'points', parseInt(e.target.value))}
                    min="1"
                  />
                </div>
              </div>

              {q.type === 'multiple_choice' && (
                <div className="form-group">
                  <label>Options</label>
                  {q.options?.map((opt, optIdx) => (
                    <input
                      key={optIdx}
                      type="text"
                      value={opt}
                      onChange={e => updateOption(qIdx, optIdx, e.target.value)}
                      placeholder={`Option ${optIdx + 1}`}
                      style={{ marginBottom: '8px' }}
                    />
                  ))}
                </div>
              )}

              {q.type === 'true_false' && (
                <div className="form-group">
                  <label>Correct Answer</label>
                  <select value={q.correct_answer} onChange={e => updateQuestion(qIdx, 'correct_answer', e.target.value)}>
                    <option value="">Select...</option>
                    <option value="true">True</option>
                    <option value="false">False</option>
                  </select>
                </div>
              )}

              {q.type === 'short_answer' && (
                <div className="form-group">
                  <label>Correct Answer</label>
                  <input
                    type="text"
                    value={q.correct_answer}
                    onChange={e => updateQuestion(qIdx, 'correct_answer', e.target.value)}
                    placeholder="Enter the correct answer..."
                  />
                </div>
              )}

              {q.type === 'multiple_choice' && (
                <div className="form-group">
                  <label>Correct Answer</label>
                  <select value={q.correct_answer} onChange={e => updateQuestion(qIdx, 'correct_answer', e.target.value)}>
                    <option value="">Select correct option...</option>
                    {q.options?.filter(o => o).map((opt, i) => (
                      <option key={i} value={opt}>{opt}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          ))}
          
          <button type="button" onClick={addQuestion} className="btn-add-module">+ Add Question</button>
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => router.back()} className="btn-secondary">Cancel</button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Creating...' : 'Create Quiz'}
          </button>
        </div>
      </form>
    </div>
  )
}