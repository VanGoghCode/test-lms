'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '../auth-context'
import { useRouter } from 'next/navigation'

interface Notification {
  id: number
  type: string
  title: string
  message: string
  link: string | null
  read: boolean
  created_at: string
}

interface NotificationPreferences {
  email_assignments: boolean
  email_announcements: boolean
  email_grades: boolean
  email_discussions: boolean
  push_assignments: boolean
  push_announcements: boolean
  push_grades: boolean
  push_discussions: boolean
}

export default function NotificationsPage() {
  const { user, token } = useAuth()
  const router = useRouter()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null)
  const [showPreferences, setShowPreferences] = useState(false)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    fetchNotifications()
    fetchPreferences()
  }, [user, router])

  const fetchNotifications = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/notifications', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setNotifications(data)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchPreferences = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/notifications/preferences', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setPreferences(data)
      }
    } catch (error) {
      console.error('Failed to fetch preferences:', error)
    }
  }

  const markAsRead = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/notifications/${id}/read`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        setNotifications(notifications.map(n => 
          n.id === id ? { ...n, read: true } : n
        ))
      }
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/notifications/mark-all-read', {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        setNotifications(notifications.map(n => ({ ...n, read: true })))
      }
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  const deleteNotification = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/notifications/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        setNotifications(notifications.filter(n => n.id !== id))
      }
    } catch (error) {
      console.error('Failed to delete notification:', error)
    }
  }

  const updatePreferences = async (newPreferences: NotificationPreferences) => {
    try {
      const response = await fetch('http://localhost:8000/api/notifications/preferences', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newPreferences)
      })
      if (response.ok) {
        setPreferences(newPreferences)
      }
    } catch (error) {
      console.error('Failed to update preferences:', error)
    }
  }

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id)
    }
    if (notification.link) {
      router.push(notification.link)
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'assignment': return '📝'
      case 'announcement': return '📢'
      case 'grade': return '📊'
      case 'discussion': return '💬'
      case 'course_update': return '📚'
      case 'certificate': return '🎓'
      default: return '🔔'
    }
  }

  const filteredNotifications = filter === 'unread' 
    ? notifications.filter(n => !n.read)
    : notifications

  if (loading) {
    return <div className="loading">Loading notifications...</div>
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Notifications</h1>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => setShowPreferences(!showPreferences)}>
            ⚙️ Preferences
          </button>
          <button className="btn-secondary" onClick={markAllAsRead}>
            Mark All Read
          </button>
        </div>
      </div>

      {showPreferences && preferences && (
        <div className="preferences-panel">
          <h2>Notification Preferences</h2>
          <div className="preferences-grid">
            <div className="preference-section">
              <h3>Email Notifications</h3>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.email_assignments}
                  onChange={(e) => updatePreferences({ ...preferences, email_assignments: e.target.checked })}
                />
                Assignments
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.email_announcements}
                  onChange={(e) => updatePreferences({ ...preferences, email_announcements: e.target.checked })}
                />
                Announcements
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.email_grades}
                  onChange={(e) => updatePreferences({ ...preferences, email_grades: e.target.checked })}
                />
                Grades
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.email_discussions}
                  onChange={(e) => updatePreferences({ ...preferences, email_discussions: e.target.checked })}
                />
                Discussions
              </label>
            </div>
            <div className="preference-section">
              <h3>Push Notifications</h3>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.push_assignments}
                  onChange={(e) => updatePreferences({ ...preferences, push_assignments: e.target.checked })}
                />
                Assignments
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.push_announcements}
                  onChange={(e) => updatePreferences({ ...preferences, push_announcements: e.target.checked })}
                />
                Announcements
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.push_grades}
                  onChange={(e) => updatePreferences({ ...preferences, push_grades: e.target.checked })}
                />
                Grades
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={preferences.push_discussions}
                  onChange={(e) => updatePreferences({ ...preferences, push_discussions: e.target.checked })}
                />
                Discussions
              </label>
            </div>
          </div>
        </div>
      )}

      <div className="filter-tabs">
        <button 
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All ({notifications.length})
        </button>
        <button 
          className={filter === 'unread' ? 'active' : ''}
          onClick={() => setFilter('unread')}
        >
          Unread ({notifications.filter(n => !n.read).length})
        </button>
      </div>

      {filteredNotifications.length === 0 ? (
        <div className="empty-state">
          <h2>No notifications</h2>
          <p>You're all caught up!</p>
        </div>
      ) : (
        <div className="notifications-list">
          {filteredNotifications.map(notification => (
            <div 
              key={notification.id} 
              className={`notification-item ${notification.read ? 'read' : 'unread'}`}
              onClick={() => handleNotificationClick(notification)}
            >
              <div className="notification-icon">
                {getNotificationIcon(notification.type)}
              </div>
              <div className="notification-content">
                <h3>{notification.title}</h3>
                <p>{notification.message}</p>
                <span className="notification-time">{notification.created_at}</span>
              </div>
              <div className="notification-actions">
                {!notification.read && (
                  <button 
                    className="btn-icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      markAsRead(notification.id)
                    }}
                    title="Mark as read"
                  >
                    ✓
                  </button>
                )}
                <button 
                  className="btn-icon"
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteNotification(notification.id)
                  }}
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
