'use client'
import { useAuth } from '../../../auth-context'
import { useRouter, useParams, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Attempt {
  score: number
  total_points: number
  percentage: number
  passed: boolean
  submitted_at: string
  results: {
    question_id: number
    question: string
    your_answer: string
    correct_answer: string
    is_correct: boolean
    points: number
  }[]
}

export default function QuizResults() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [attempts, setAttempts] = useState<Attempt[]>([])
  const [loading, setLoading] = useState(true)
  const score = searchParams.get('score')

  useEffect(() => {
    if (authLoading) return
    
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/quizzes/${params.id}/attempts`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setAttempts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [params.id, user, token, authLoading, router])

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  const latestAttempt = attempts[attempts.length - 1]

  if (!latestAttempt) {
    return <div className="container"><p>No attempts found</p></div>
  }

  return (
    <div className="quiz-results">
      <div className="results-header">
        <h1>Quiz Results</h1>
        {score && (
          <div className={`score-badge ${latestAttempt.passed ? 'passed' : 'failed'}`}>
            {latestAttempt.percentage}%
          </div>
        )}
      </div>

      <div className="results-summary">
        <div className="summary-card">
          <h3>Score</h3>
          <p className="big-number">{latestAttempt.score}/{latestAttempt.total_points}</p>
        </div>
        <div className="summary-card">
          <h3>Percentage</h3>
          <p className="big-number">{latestAttempt.percentage}%</p>
        </div>
        <div className="summary-card">
          <h3>Status</h3>
          <p className={`status ${latestAttempt.passed ? 'passed' : 'failed'}`}>
            {latestAttempt.passed ? '✓ Passed' : '✗ Failed'}
          </p>
        </div>
      </div>

      <h2>Question Review</h2>
      <div className="results-list">
        {latestAttempt.results.map((result, idx) => (
          <div key={result.question_id} className={`result-card ${result.is_correct ? 'correct' : 'incorrect'}`}>
            <div className="result-header">
              <h3>Question {idx + 1}</h3>
              <span className={`result-badge ${result.is_correct ? 'correct' : 'incorrect'}`}>
                {result.is_correct ? '✓ Correct' : '✗ Incorrect'}
              </span>
            </div>
            <p className="question-text">{result.question}</p>
            <div className="answer-comparison">
              <div className="your-answer">
                <strong>Your Answer:</strong>
                <p>{result.your_answer || '(No answer)'}</p>
              </div>
              {!result.is_correct && (
                <div className="correct-answer">
                  <strong>Correct Answer:</strong>
                  <p>{result.correct_answer}</p>
                </div>
              )}
            </div>
            <p className="points">Points: {result.points}</p>
          </div>
        ))}
      </div>

      <div className="results-actions">
        <button onClick={() => router.push('/courses')} className="btn-primary">
          Back to Courses
        </button>
      </div>
    </div>
  )
}