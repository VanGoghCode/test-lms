'use client'
import { useAuth } from '../auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Course {
  id: number
  title: string
  description: string
  category: string
  thumbnail: string
  duration: string
  status: string
  instructor: { id: number; name: string; avatar: string }
}

export default function InstructorDashboard() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [courses, setCourses] = useState<Course[]>([])
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
    fetch(`${baseUrl}/api/instructor/courses`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setCourses)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user, token, authLoading, router])

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  const handlePublish = async (courseId: number) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    await fetch(`${baseUrl}/api/courses/${courseId}/publish`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    setCourses(courses.map(c => c.id === courseId ? { ...c, status: 'published' } : c))
  }

  const handleUnpublish = async (courseId: number) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    await fetch(`${baseUrl}/api/courses/${courseId}/unpublish`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    setCourses(courses.map(c => c.id === courseId ? { ...c, status: 'draft' } : c))
  }

  return (
    <>
      <div className="page-header">
        <h1>Instructor Dashboard</h1>
        <a href="/instructor/courses/new" className="btn-primary">Create New Course</a>
      </div>

      <h2>My Courses</h2>
      {courses.length === 0 ? (
        <p className="empty-state">No courses yet. Create your first course!</p>
      ) : (
        <div className="grid">
          {courses.map(course => (
            <div key={course.id} className="card">
              <div className="card-thumbnail" style={{ background: course.thumbnail }}>
                {course.title.charAt(0)}
              </div>
              <div className="card-body">
                <h3 className="card-title">{course.title}</h3>
                <p className="card-meta">{course.category} • {course.duration}</p>
                <span className={`badge badge-${course.status === 'published' ? 'success' : 'warning'}`}>
                  {course.status}
                </span>
                <div className="card-actions">
                  <a href={`/instructor/courses/${course.id}/edit`} className="btn-secondary">Edit</a>
                  {course.status === 'draft' ? (
                    <button onClick={() => handlePublish(course.id)} className="btn-primary">Publish</button>
                  ) : (
                    <button onClick={() => handleUnpublish(course.id)} className="btn-secondary">Unpublish</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}