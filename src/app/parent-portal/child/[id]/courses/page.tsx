'use client'
import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '../../../auth-context'

interface Course {
  course_id: number
  course_title: string
  instructor_name: string
  progress: number
  completed_lessons: number
  total_lessons: number
  enrolled_at: string
  category: string
  level: string
}

export default function ParentChildCoursesPage() {
  const params = useParams()
  const router = useRouter()
  const { user, token } = useAuth()
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    fetchCourses()
  }, [user, router])

  const fetchCourses = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/parent/child/${params.id}/courses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setCourses(data)
      }
    } catch (error) {
      console.error('Failed to fetch courses:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading courses...</div>
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <button className="btn-back" onClick={() => router.push('/parent-portal')}>
          ← Back to Dashboard
        </button>
        <h1>Child's Courses</h1>
      </div>

      {courses.length === 0 ? (
        <div className="empty-state">
          <h2>No courses enrolled</h2>
          <p>Your child hasn't enrolled in any courses yet</p>
        </div>
      ) : (
        <div className="courses-table">
          <table>
            <thead>
              <tr>
                <th>Course</th>
                <th>Instructor</th>
                <th>Category</th>
                <th>Level</th>
                <th>Progress</th>
                <th>Lessons</th>
                <th>Enrolled</th>
              </tr>
            </thead>
            <tbody>
              {courses.map(course => (
                <tr key={course.course_id}>
                  <td className="course-title">{course.course_title}</td>
                  <td>{course.instructor_name}</td>
                  <td><span className="badge">{course.category}</span></td>
                  <td><span className={`badge badge-${course.level}`}>{course.level}</span></td>
                  <td>
                    <div className="progress-cell">
                      <div className="progress-bar small">
                        <div className="progress-fill" style={{ width: `${course.progress}%` }} />
                      </div>
                      <span>{course.progress}%</span>
                    </div>
                  </td>
                  <td>{course.completed_lessons}/{course.total_lessons}</td>
                  <td>{course.enrolled_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
