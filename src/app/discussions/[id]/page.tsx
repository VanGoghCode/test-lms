'use client'
import { useAuth } from '../../auth-context'
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
}

interface Reply {
  id: number
  post_id: number
  user_id: number
  user_name: string
  user_avatar: string
  content: string
  created_at: string
  upvotes: number
}

export default function DiscussionDetail() {
  const params = useParams()
  const router = useRouter()
  const { user, token, isLoading: authLoading } = useAuth()
  const [post, setPost] = useState<Post | null>(null)
  const [replies, setReplies] = useState<Reply[]>([])
  const [replyContent, setReplyContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/discussions/${params.id}`)
      .then(r => r.json())
      .then(data => {
        setPost(data.post)
        setReplies(data.replies)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [params.id, authLoading])

  const handleUpvotePost = async () => {
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const res = await fetch(`${baseUrl}/api/discussions/${params.id}/upvote`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (post) setPost({ ...post, upvotes: data.upvotes })
  }

  const handleUpvoteReply = async (replyId: number) => {
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const res = await fetch(`${baseUrl}/api/discussions/${params.id}/replies/${replyId}/upvote`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await res.json()
    
    setReplies(replies.map(r => r.id === replyId ? { ...r, upvotes: data.upvotes } : r))
  }

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user || !token) {
      router.push('/login')
      return
    }

    setSubmitting(true)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(`${baseUrl}/api/discussions/${params.id}/replies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: replyContent })
      })

      const newReply = await res.json()
      setReplies([...replies, newReply])
      setReplyContent('')
    } catch (err) {
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading || loading || !post) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <div className="discussion-detail">
      <div className="post-card">
        <div className="post-votes">
          <button onClick={handleUpvotePost} className="vote-btn">▲</button>
          <span className="vote-count">{post.upvotes}</span>
        </div>
        <div className="post-content">
          {post.is_pinned && <span className="pinned-badge">📌 Pinned</span>}
          <h1>{post.title}</h1>
          <div className="post-meta">
            <span className="author">
              <span className="avatar-small">{post.user_avatar}</span>
              {post.user_name}
            </span>
            <span>{post.created_at}</span>
          </div>
          <p className="post-body">{post.content}</p>
        </div>
      </div>

      <div className="replies-section">
        <h2>{replies.length} Replies</h2>
        
        {user && (
          <form onSubmit={handleReply} className="reply-form">
            <textarea
              value={replyContent}
              onChange={e => setReplyContent(e.target.value)}
              required
              rows={4}
              placeholder="Write your reply..."
            />
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Posting...' : 'Post Reply'}
            </button>
          </form>
        )}

        <div className="replies-list">
          {replies.map(reply => (
            <div key={reply.id} className="reply-card">
              <div className="reply-votes">
                <button onClick={() => handleUpvoteReply(reply.id)} className="vote-btn">▲</button>
                <span className="vote-count">{reply.upvotes}</span>
              </div>
              <div className="reply-content">
                <div className="reply-meta">
                  <span className="author">
                    <span className="avatar-small">{reply.user_avatar}</span>
                    {reply.user_name}
                  </span>
                  <span>{reply.created_at}</span>
                </div>
                <p className="reply-body">{reply.content}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}