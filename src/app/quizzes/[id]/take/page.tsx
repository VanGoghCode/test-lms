'use client'
import { useAuth } from '../../../auth-context'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Quiz {
  id: number
  title: string
  course_name: string
  description: string
  time_limit?: number
  total_points: number
  passing_score: number
}

interface Question {
  id: number
  question: string
  type: string
  options?: string[]
  points: number
}

interface Answer {
  question_id: number
  answer: string
}

export default function TakeQuiz() {
  const params = useParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [answers, setAnswers] = useState<Answer[]>([])
  const [timeLeft, setTimeLeft] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    Promise.all([
      fetch(`${baseUrl}/api/quizzes/${params.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(r => r.json()),
      fetch(`${baseUrl}/api/quizzes/${params.id}/questions`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(r => r.json())
    ])
      .then(([quizData, questionsData]) => {
        setQuiz(quizData)
        setQuestions(questionsData)
        if (quizData.time_limit) {
          setTimeLeft(quizData.time_limit * 60) // Convert to seconds
        }
        setAnswers(questionsData.map((q: Question) => ({ question_id: q.id, answer: '' })))
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [params.id, user, token, authLoading, router])

  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev === null || prev <= 1) {
          handleSubmit()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [timeLeft])

  const updateAnswer = (questionId: number, answer: string) => {
    setAnswers(answers.map(a => 
      a.question_id === questionId ? { ...a, answer } : a
    ))
  }

  const handleSubmit = async () => {
    if (submitting) return
    setSubmitting(true)

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    try {
      const res = await fetch(`${baseUrl}/api/quizzes/${params.id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          quiz_id: Number(params.id),
          answers: answers.filter(a => a.answer)
        })
      })

      const result = await res.json()
      router.push(`/quizzes/${params.id}/results?score=${result.percentage}`)
    } catch (err) {
      console.error(err)
      alert('Failed to submit quiz')
    } finally {
      setSubmitting(false)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (authLoading || loading || !quiz) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <div className="quiz-take">
      <div className="quiz-header">
        <div>
          <h1>{quiz.title}</h1>
          <p className="subtitle">{quiz.course_name}</p>
        </div>
        {timeLeft !== null && (
          <div className={`timer ${timeLeft < 60 ? 'warning' : ''}`}>
            ⏱️ {formatTime(timeLeft)}
          </div>
        )}
      </div>

      <div className="quiz-info-bar">
        <span>{questions.length} questions</span>
        <span>{quiz.total_points} points</span>
        <span>{quiz.passing_score}% to pass</span>
      </div>

      <div className="questions-container">
        {questions.map((q, idx) => (
          <div key={q.id} className="question-card">
            <h3>Question {idx + 1} ({q.points} {q.points === 1 ? 'point' : 'points'})</h3>
            <p className="question-text">{q.question}</p>

            {q.type === 'multiple_choice' && (
              <div className="options">
                {q.options?.map((opt, i) => (
                  <label key={i} className="option-label">
                    <input
                      type="radio"
                      name={`question-${q.id}`}
                      value={opt}
                      checked={answers.find(a => a.question_id === q.id)?.answer === opt}
                      onChange={e => updateAnswer(q.id, e.target.value)}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}

            {q.type === 'true_false' && (
              <div className="options">
                <label className="option-label">
                  <input
                    type="radio"
                    name={`question-${q.id}`}
                    value="true"
                    checked={answers.find(a => a.question_id === q.id)?.answer === 'true'}
                    onChange={e => updateAnswer(q.id, e.target.value)}
                  />
                  <span>True</span>
                </label>
                <label className="option-label">
                  <input
                    type="radio"
                    name={`question-${q.id}`}
                    value="false"
                    checked={answers.find(a => a.question_id === q.id)?.answer === 'false'}
                    onChange={e => updateAnswer(q.id, e.target.value)}
                  />
                  <span>False</span>
                </label>
              </div>
            )}

            {q.type === 'short_answer' && (
              <input
                type="text"
                className="short-answer-input"
                value={answers.find(a => a.question_id === q.id)?.answer || ''}
                onChange={e => updateAnswer(q.id, e.target.value)}
                placeholder="Type your answer..."
              />
            )}
          </div>
        ))}
      </div>

      <div className="quiz-actions">
        <button onClick={handleSubmit} className="btn-primary" disabled={submitting}>
          {submitting ? 'Submitting...' : 'Submit Quiz'}
        </button>
      </div>
    </div>
  )
}