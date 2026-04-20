'use client'
import { useState } from 'react'
import { useAuth } from '../../auth-context'
import { useRouter } from 'next/navigation'

export default function ParentVerifyPage() {
  const { user, token } = useAuth()
  const router = useRouter()
  const [verificationCode, setVerificationCode] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    try {
      const response = await fetch(`http://localhost:8000/api/parent/verify/${verificationCode}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Verification failed')
      }

      setMessage(`Successfully linked to ${data.parent_name}!`)
      setTimeout(() => router.push('/parent-portal/my-parents'), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    router.push('/login')
    return null
  }

  return (
    <div className="page-container">
      <div className="verify-container">
        <div className="verify-card">
          <h1>Verify Parent Link</h1>
          <p>Enter the verification code sent by your parent to link your accounts</p>

          {message && <div className="success-message">{message}</div>}
          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleVerify}>
            <div className="form-group">
              <label htmlFor="code">Verification Code</label>
              <input
                id="code"
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.toUpperCase())}
                placeholder="Enter 12-character code"
                maxLength={12}
                required
                className="code-input"
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify Link'}
            </button>
          </form>

          <div className="info-section">
            <h3>How does this work?</h3>
            <ul>
              <li>Your parent/guardian requests to link to your account</li>
              <li>They receive a verification code</li>
              <li>They share the code with you</li>
              <li>Enter the code here to complete the link</li>
            </ul>
            <p className="privacy-note">
              Once linked, your parent will be able to view your course progress, 
              assignments, and grades. They cannot modify your account or courses.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
