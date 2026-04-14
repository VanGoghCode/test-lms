'use client'
import { useAuth } from '../../../auth-context'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Post {
  id: number
  course_id: number
  user_id: number
  user_name: string
  user_avatar: string
  title: string
  content: string
  created_at: string
  upvotes: number
  is_pinned: boolean
  reply_count: number
}

export default function CourseDiscussions() {
  const params = useParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/courses/${params.id}/discussions`)
      .then(r => r.json())
      .then(setPosts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [params.id, authLoading])

  const handleUpvote = async (postId: number) => {
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const res = await fetch(`${baseUrl}/api/discussions/${postId}/upvote`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await res.json()
    
    setPosts(posts.map(p => p.id === postId ? { ...p, upvotes: data.upvotes } : p))
  }

  const handlePin = async (postId: number) => {
    if (!user || !token) return

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const res = await fetch(`${baseUrl}/api/discussions/${postId}/pin`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await res.json()
    
    setPosts(posts.map(p => p.id === postId ? { ...p, is_pinned: data.pinned } : p))
  }

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <>
      <div className="page-header">
        <h1>Course Discussions</h1>
        {user && (
          <a href={`/courses/${params.id}/discussions/new`} className="btn-primary">New Discussion</a>
        )}
      </div>

      {posts.length === 0 ? (
        <p className="empty-state">No discussions yet. Start the conversation!</p>
      ) : (
        <div className="discussions-list">
          {posts.map(post => (
            <div key={post.id} className="discussion-card">
              <div className="discussion-votes">
                <button onClick={() => handleUpvote(post.id)} className="vote-btn">▲</button>
                <span className="vote-count">{post.upvotes}</span>
              </div>
              <div className="discussion-content">
                <div className="discussion-header">
                  {post.is_pinned && <span className="pinned-badge">📌 Pinned</span>}
                  <a href={`/discussions/${post.id}`} className="discussion-title">{post.title}</a>
                </div>
                <p className="discussion-preview">{post.content.substring(0, 150)}...</p>
                <div className="discussion-meta">
                  <span className="author">
                    <span className="avatar-small">{post.user_avatar}</span>
                    {post.user_name}
                  </span>
                  <span>{post.created_at}</span>
                  <span>💬 {post.reply_count} replies</span>
                  {(user?.role === 'instructor' || user?.role === 'admin') && (
                    <button onClick={() => handlePin(post.id)} className="pin-btn">
                      {post.is_pinned ? 'Unpin' : 'Pin'}
                    </button>
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