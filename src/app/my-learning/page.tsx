'use client'

import { useState, useEffect } from 'react'

interface Enrollment {
  id: number
  course_id: number
  progress: number
  course: {
    id: number
    title: string
    instructor: { name: string }
    thumbnail: string
  }
}

export default function MyLearning() {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([])

  useEffect(() => {
    fetch('http://localhost:8000/api/users/1/enrollments')
      .then(r => r.json())
      .then(setEnrollments)
  }, [])

  return (
    <>
      <h1>My Learning</h1>
      <p className="subtitle">Your enrolled courses</p>

      {enrollments.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)' }}>You haven't enrolled in any courses yet.</p>
      ) : (
        <div className="grid">
          {enrollments.map(enrollment => (
            <a href={`/courses/${enrollment.course_id}`} key={enrollment.id} className="card">
              <div className="card-thumbnail" style={{ background: enrollment.course.thumbnail }}>
                {enrollment.course.title.charAt(0)}
              </div>
              <div className="card-body">
                <h3 className="card-title">{enrollment.course.title}</h3>
                <p className="card-meta">{enrollment.course.instructor.name}</p>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${enrollment.progress}%` }} />
                </div>
                <p style={{ marginTop: 8, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  {enrollment.progress}% complete
                </p>
              </div>
            </a>
          ))}
        </div>
      )}
    </>
  )
}