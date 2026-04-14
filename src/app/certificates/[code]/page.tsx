'use client'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Certificate {
  id: number
  user_name: string
  course_name: string
  instructor_name: string
  issued_at: string
  verification_code: string
  completion_date: string
}

export default function CertificateView() {
  const params = useParams()
  const [certificate, setCertificate] = useState<Certificate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/api/certificates/verify/${params.code}`)
      .then(r => {
        if (!r.ok) throw new Error('Certificate not found')
        return r.json()
      })
      .then(setCertificate)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [params.code])

  const handlePrint = () => {
    window.print()
  }

  if (loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  if (error || !certificate) {
    return (
      <div className="container">
        <div className="error-state">
          <h1>Certificate Not Found</h1>
          <p>The verification code you entered is invalid or the certificate does not exist.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="certificate-view">
      <div className="certificate-actions no-print">
        <button onClick={handlePrint} className="btn-primary">🖨️ Print Certificate</button>
        <a href="/certificates" className="btn-secondary">← Back to Certificates</a>
      </div>

      <div className="certificate-document">
        <div className="certificate-border">
          <div className="certificate-content">
            <div className="certificate-logo">🎓</div>
            <h1 className="certificate-heading">Certificate of Completion</h1>
            <p className="certificate-subtitle">This is to certify that</p>
            
            <h2 className="certificate-name">{certificate.user_name}</h2>
            
            <p className="certificate-text">has successfully completed the course</p>
            
            <h3 className="certificate-course">{certificate.course_name}</h3>
            
            <div className="certificate-details">
              <div className="detail-item">
                <span className="detail-label">Instructor:</span>
                <span className="detail-value">{certificate.instructor_name}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Completion Date:</span>
                <span className="detail-value">{certificate.completion_date}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Issue Date:</span>
                <span className="detail-value">{certificate.issued_at}</span>
              </div>
            </div>

            <div className="certificate-verification">
              <p className="verification-label">Verification Code</p>
              <p className="verification-code">{certificate.verification_code}</p>
              <p className="verification-url">Verify at: {window.location.origin}/certificates/{certificate.verification_code}</p>
            </div>

            <div className="certificate-seal">
              <div className="seal">✓</div>
              <p>Official Certificate</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}