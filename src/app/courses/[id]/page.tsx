'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'

interface Course {
  id: number
  title: string
  description: string
  instructor: { id: number; name: string; avatar: string }
  category: string
  thumbnail: string
  duration: string
  modules: { id: number; title: string; lessons: { id: number; title: string; duration: string }[] }[]
}

interface Enrollment {
  id: number
  course_id: number
  progress: number
}

export default function CourseDetail() {
  const params = useParams()
  const [course, setCourse] = useState<Course | null>(null)
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null)

  useEffect(() => {
    fetch(`http://localhost:8000/api/courses/${params.id}`)
      .then(r => r.json())
      .then(setCourse)

    fetch('http://localhost:8000/api/users/1/enrollments')
      .then(r => r.json())
      .then(enrollments => {
        const found = enrollments.find((e: any) => e.course_id === Number(params.id))
        setEnrollment(found || null)
      })
  }, [params.id])

  const handleEnroll = async () => {
    await fetch(`http://localhost:8000/api/courses/${params.id}/enroll?user_id=1`, { method: 'POST' })
    window.location.reload()
  }

  if (!course) return <div>Loading...</div>

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
        <h2>Course Content</h2>
        {course.modules.map(module => (
          <div key={module.id} className="module">
            <div className="module-header">{module.title}</div>
            {module.lessons.map(lesson => (
              <div key={lesson.id} className="lesson">
                <span>{lesson.title}</span>
                <span>{lesson.duration}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="course-sidebar">
        <div className="enroll-card">
          {enrollment ? (
            <>
              <p>Your Progress</p>
              <div className="progress-bar" style={{ marginTop: 12 }}>
                <div className="progress-fill" style={{ width: `${enrollment.progress}%` }} />
              </div>
              <p style={{ marginTop: 8, color: 'var(--text-secondary)' }}>{enrollment.progress}% complete</p>
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