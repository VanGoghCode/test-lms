'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '../auth-context'
import { useRouter } from 'next/navigation'

interface Course {
  id: number
  title: string
  description: string
  instructor: { name: string; avatar: string }
  category: string
  level: string
  thumbnail: string
  duration: string
  average_rating: number
  rating_count: number
}

export default function WishlistPage() {
  const { user, token } = useAuth()
  const router = useRouter()
  const [wishlist, setWishlist] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    fetchWishlist()
  }, [user, router])

  const fetchWishlist = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/wishlist', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setWishlist(data)
      }
    } catch (error) {
      console.error('Failed to fetch wishlist:', error)
    } finally {
      setLoading(false)
    }
  }

  const removeFromWishlist = async (courseId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/wishlist/${courseId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        setWishlist(wishlist.filter(c => c.id !== courseId))
      }
    } catch (error) {
      console.error('Failed to remove from wishlist:', error)
    }
  }

  if (loading) {
    return <div className="loading">Loading wishlist...</div>
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>My Wishlist</h1>
        <p>Courses you've saved for later</p>
      </div>

      {wishlist.length === 0 ? (
        <div className="empty-state">
          <h2>Your wishlist is empty</h2>
          <p>Browse courses and add them to your wishlist to save for later</p>
          <button className="btn-primary" onClick={() => router.push('/courses')}>
            Browse Courses
          </button>
        </div>
      ) : (
        <div className="courses-grid">
          {wishlist.map(course => (
            <div key={course.id} className="course-card">
              <div className="course-thumbnail" style={{ background: course.thumbnail }}></div>
              <div className="course-content">
                <div className="course-meta">
                  <span className="category">{course.category}</span>
                  <span className="level">{course.level}</span>
                </div>
                <h3>{course.title}</h3>
                <p className="course-description">{course.description}</p>
                <div className="course-instructor">
                  <div className="avatar">{course.instructor.avatar}</div>
                  <span>{course.instructor.name}</span>
                </div>
                <div className="course-stats">
                  <span>⭐ {course.average_rating.toFixed(1)} ({course.rating_count})</span>
                  <span>⏱️ {course.duration}</span>
                </div>
                <div className="course-actions">
                  <button 
                    className="btn-primary"
                    onClick={() => router.push(`/courses/${course.id}`)}
                  >
                    View Course
                  </button>
                  <button 
                    className="btn-secondary"
                    onClick={() => removeFromWishlist(course.id)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
