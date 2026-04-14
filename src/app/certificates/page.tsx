'use client'
import { useAuth } from '../auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Certificate {
  id: number
  user_id: number
  user_name: string
  course_id: number
  course_name: string
  instructor_name: string
  issued_at: string
  verification_code: string
  completion_date: string
}

export default function CertificatesPage() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [certificates, setCertificates] = useState<Certificate[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    
    if (!user || !token) {
      router.push('/login')
      return
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/users/${user.id}/certificates`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setCertificates)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user, token, authLoading, router])

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  return (
    <>
      <h1>My Certificates</h1>
      <p className="subtitle">Your earned course completion certificates</p>

      {certificates.length === 0 ? (
        <p className="empty-state">No certificates yet. Complete courses to earn certificates!</p>
      ) : (
        <div className="certificates-grid">
          {certificates.map(cert => (
            <a key={cert.id} href={`/certificates/${cert.verification_code}`} className="certificate-card">
              <div className="certificate-header">
                <span className="certificate-icon">🏆</span>
                <h3>{cert.course_name}</h3>
              </div>
              <div className="certificate-body">
                <p className="instructor">Instructor: {cert.instructor_name}</p>
                <p className="issued-date">Issued: {cert.issued_at}</p>
                <p className="verification">Code: {cert.verification_code}</p>
              </div>
              <div className="certificate-footer">
                <span className="view-link">View Certificate →</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </>
  )
}