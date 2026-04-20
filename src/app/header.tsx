'use client'
import { useAuth } from './auth-context'
import { useRouter } from 'next/navigation'

export function Header() {
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <header className="header">
      <div className="container header-content">
        <a href="/" className="logo">LMS</a>
        <nav className="nav">
          <a href="/courses">Courses</a>
          {user && <a href="/my-learning">My Learning</a>}
          {user && <a href="/wishlist">Wishlist</a>}
          {user && <a href="/notifications">Notifications</a>}
          {user && <a href="/alerts">Alerts</a>}
          {user && <a href="/assignments">Assignments</a>}
          {user && <a href="/certificates">Certificates</a>}
          {(user?.role === 'instructor' || user?.role === 'admin') && (
            <>
              <a href="/instructor">Instructor</a>
              <a href="/instructor/analytics">Analytics</a>
              <a href="/instructor/assignments">Grading</a>
              <a href="/instructor/reviews">Reviews</a>
              <a href="/instructor/quizzes">Quizzes</a>
            </>
          )}
        </nav>
        {user ? (
          <div className="user-menu">
            <span className="user-avatar">{user.avatar}</span>
            <span className="user-name">{user.name}</span>
            <button onClick={handleLogout} className="btn-link">Logout</button>
          </div>
        ) : (
          <div className="auth-buttons">
            <a href="/login" className="btn-secondary">Login</a>
            <a href="/register" className="btn-primary">Sign Up</a>
          </div>
        )}
      </div>
    </header>
  )
}