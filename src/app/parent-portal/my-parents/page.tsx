'use client'
import { useState, useEffect } from 'react'
import { useAuth } from '../../auth-context'
import { useRouter } from 'next/navigation'

interface Parent {
  parent_id: number
  parent_name: string
  parent_email: string
  relation: string
  linked_at: string
}

export default function MyParentsPage() {
  const { user, token } = useAuth()
  const router = useRouter()
  const [parents, setParents] = useState<Parent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      router.push('/login')
      return
    }
    fetchParents()
  }, [user, router])

  const fetchParents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/child/parents', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setParents(data)
      }
    } catch (error) {
      console.error('Failed to fetch parents:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>My Parents/Guardians</h1>
        <p>Manage who can view your learning progress</p>
      </div>

      {parents.length === 0 ? (
        <div className="empty-state">
          <h2>No parents linked</h2>
          <p>Your parents can request to link to your account to monitor your progress</p>
          <button className="btn-primary" onClick={() => router.push('/parent-portal/verify')}>
            Verify a Parent Link
          </button>
        </div>
      ) : (
        <div className="parents-list">
          {parents.map(parent => (
            <div key={parent.parent_id} className="parent-card">
              <div className="parent-avatar">
                {parent.parent_name.split(' ').map(n => n[0]).join('').toUpperCase()}
              </div>
              <div className="parent-info">
                <h3>{parent.parent_name}</h3>
                <span className="relation">{parent.relation}</span>
                <span className="email">{parent.parent_email}</span>
              </div>
              <div className="linked-date">
                <span className="label">Linked</span>
                <span className="date">{parent.linked_at}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="info-box">
        <h3>What can parents see?</h3>
        <ul>
          <li>Your enrolled courses and progress</li>
          <li>Assignment submissions and grades</li>
          <li>Upcoming and overdue assignments</li>
          <li>Recent learning activity</li>
        </ul>
        <p className="note">Parents cannot modify your account, courses, or submissions.</p>
      </div>
    </div>
  )
}
