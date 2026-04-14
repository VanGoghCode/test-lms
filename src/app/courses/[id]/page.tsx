'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '../../auth-context'

interface Course {
  id: number
  title: string
  description: string
  instructor: { id: number; name: string; avatar: string }
  category: string
  thumbnail: string
  duration: string
  modules: { id: number; title: string; lessons: { id: number; title: string; duration: string; video_url?: string }[] }[]
}

interface Progress {
  course_id: number
  completed_lessons: number[]
  total_lessons: number
  progress_percent: number
}

export default function CourseDetail() {
  const params = useParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [course, setCourse] = useState<Course | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [enrolled, setEnrolled] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    fetch(`${baseUrl}/api/courses/${params.id}`)
      .then(r => r.json())
      .then(setCourse)

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
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [params.id, user, token, authLoading])

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

    // Refresh progress
    const res = await fetch(`${baseUrl}/api/courses/${params.id}/progress`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    setProgress(await res.json())
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
            </>
          ) : (
            <>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>Not enrolled yet</p>
              <button className="btn btn-primary" onClick={handleEnroll}>Enroll Now</button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}