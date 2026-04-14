'use client'
import { useAuth } from '../../auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Quiz {
  id: number
  title: string
  course_id: number
  course_name: string
  description: string
  time_limit?: number
  total_points: number
  passing_score: number
}

export default function InstructorQuizzes() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [loading, setLoading] = useState(true)

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
    fetch(`${baseUrl}/api/instructor/quizzes`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setQuizzes)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user, token, authLoading, router])

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <>
      <div className="page-header">
        <h1>Quiz Management</h1>
        <a href="/instructor/quizzes/new" className="btn-primary">Create New Quiz</a>
      </div>

      {quizzes.length === 0 ? (
        <p className="empty-state">No quizzes yet. Create your first quiz!</p>
      ) : (
        <div className="grid">
          {quizzes.map(quiz => (
            <div key={quiz.id} className="card">
              <div className="card-body">
                <h3 className="card-title">{quiz.title}</h3>
                <p className="card-meta">{quiz.course_name}</p>
                <p className="quiz-info">
                  {quiz.total_points} points • {quiz.passing_score}% to pass
                  {quiz.time_limit && ` • ${quiz.time_limit} min`}
                </p>
                <div className="card-actions">
                  <a href={`/instructor/quizzes/${quiz.id}/edit`} className="btn-secondary">Edit</a>
                  <a href={`/instructor/quizzes/${quiz.id}/results`} className="btn-primary">View Results</a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}