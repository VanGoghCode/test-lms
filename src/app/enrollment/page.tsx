'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const MAX_NAME_LENGTH = 20
const MAX_EMAIL_LENGTH = 50
const MAX_PHONE_LENGTH = 15
const MAX_ADDRESS_LENGTH = 100
const MAX_CITY_LENGTH = 50
const MAX_ZIP_LENGTH = 10

interface EnrollmentForm {
  firstName: string
  lastName: string
  email: string
  phone: string
  dateOfBirth: string
  address: string
  city: string
  state: string
  zipCode: string
  country: string
  gender: string
  race: string
  ethnicity: string
  educationLevel: string
  termsAccepted: boolean
}

const initialForm: EnrollmentForm = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  dateOfBirth: '',
  address: '',
  city: '',
  state: '',
  zipCode: '',
  country: '',
  gender: '',
  race: '',
  ethnicity: '',
  educationLevel: '',
  termsAccepted: false,
}

export default function EnrollmentPage() {
  const router = useRouter()
  const [form, setForm] = useState<EnrollmentForm>(initialForm)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    
    let limitedValue = value
    if (name === 'firstName' || name === 'lastName') {
      limitedValue = value.slice(0, MAX_NAME_LENGTH)
    } else if (name === 'email') {
      limitedValue = value.slice(0, MAX_EMAIL_LENGTH)
    } else if (name === 'phone') {
      limitedValue = value.slice(0, MAX_PHONE_LENGTH)
    } else if (name === 'address') {
      limitedValue = value.slice(0, MAX_ADDRESS_LENGTH)
    } else if (name === 'city') {
      limitedValue = value.slice(0, MAX_CITY_LENGTH)
    } else if (name === 'zipCode') {
      limitedValue = value.slice(0, MAX_ZIP_LENGTH)
    }

    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : limitedValue
    }))
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    
    if (!form.firstName.trim()) newErrors.firstName = 'First name is required'
    if (!form.lastName.trim()) newErrors.lastName = 'Last name is required'
    if (!form.email.trim()) newErrors.email = 'Email is required'
    if (!form.dateOfBirth) newErrors.dateOfBirth = 'Date of birth is required'
    if (!form.gender) newErrors.gender = 'Gender is required'
    if (!form.race) newErrors.race = 'Race is required'
    if (!form.ethnicity) newErrors.ethnicity = 'Ethnicity is required'
    if (!form.zipCode.trim()) newErrors.zipCode = 'Zip code is required'
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validate()) return
    
    setLoading(true)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('http://localhost:8000/api/enrollment/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(form)
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setResult(data)
      } else {
        setErrors({ submit: data.detail || 'Submission failed' })
      }
    } catch (err) {
      setErrors({ submit: 'Network error. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <div className="enrollment-container">
        <div className="enrollment-result-card">
          <h1>Enrollment Decision</h1>
          <div className={`decision-status ${result.decision.decision.toLowerCase()}`}>
            {result.decision.decision}
          </div>
          
          <div className="decision-details">
            <h3>Decision Details</h3>
            <p><strong>Reason:</strong> {result.decision.reason}</p>
            <p><strong>Confidence Score:</strong> {(result.decision.confidence * 100).toFixed(1)}%</p>
            
            {result.decision.scholarship_eligible && (
              <div className="scholarship-notice">
                <h4>Scholarship Eligible</h4>
                <p>{result.decision.scholarship_amount && `Awarded: $${result.decision.scholarship_amount}`}</p>
              </div>
            )}
            
            {result.decision.risk_flag && (
              <div className="risk-notice">
                <h4>At-Risk Flag</h4>
                <p>Additional support resources have been allocated.</p>
              </div>
            )}
          </div>
          
          <p className="enrollment-id">Enrollment ID: {result.enrollment_id}</p>
          <button onClick={() => router.push('/courses')} className="btn-primary">
            Browse Courses
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="enrollment-container">
      <div className="enrollment-form-card">
        <h1>Student Enrollment</h1>
        <p className="form-subtitle">Complete your enrollment to access courses</p>
        
        <form onSubmit={handleSubmit} className="enrollment-form">
          <div className="form-section">
            <h3>Personal Information</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="firstName">First Name *</label>
                <input
                  type="text"
                  id="firstName"
                  name="firstName"
                  value={form.firstName}
                  onChange={handleChange}
                  maxLength={MAX_NAME_LENGTH}
                  placeholder="Enter first name"
                  className={errors.firstName ? 'error' : ''}
                />
                <span className="char-count">{form.firstName.length}/{MAX_NAME_LENGTH}</span>
                {errors.firstName && <span className="error-text">{errors.firstName}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="lastName">Last Name *</label>
                <input
                  type="text"
                  id="lastName"
                  name="lastName"
                  value={form.lastName}
                  onChange={handleChange}
                  maxLength={MAX_NAME_LENGTH}
                  placeholder="Enter last name"
                  className={errors.lastName ? 'error' : ''}
                />
                <span className="char-count">{form.lastName.length}/{MAX_NAME_LENGTH}</span>
                {errors.lastName && <span className="error-text">{errors.lastName}</span>}
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  maxLength={MAX_EMAIL_LENGTH}
                  placeholder="Enter email"
                  className={errors.email ? 'error' : ''}
                />
                {errors.email && <span className="error-text">{errors.email}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="phone">Phone</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={form.phone}
                  onChange={handleChange}
                  maxLength={MAX_PHONE_LENGTH}
                  placeholder="Enter phone number"
                />
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="dateOfBirth">Date of Birth *</label>
              <input
                type="date"
                id="dateOfBirth"
                name="dateOfBirth"
                value={form.dateOfBirth}
                onChange={handleChange}
                className={errors.dateOfBirth ? 'error' : ''}
              />
              {errors.dateOfBirth && <span className="error-text">{errors.dateOfBirth}</span>}
            </div>
          </div>
          
          <div className="form-section">
            <h3>Address Information</h3>
            
            <div className="form-group">
              <label htmlFor="address">Street Address</label>
              <input
                type="text"
                id="address"
                name="address"
                value={form.address}
                onChange={handleChange}
                maxLength={MAX_ADDRESS_LENGTH}
                placeholder="Enter street address"
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="city">City</label>
                <input
                  type="text"
                  id="city"
                  name="city"
                  value={form.city}
                  onChange={handleChange}
                  maxLength={MAX_CITY_LENGTH}
                  placeholder="Enter city"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="state">State/Province</label>
                <input
                  type="text"
                  id="state"
                  name="state"
                  value={form.state}
                  onChange={handleChange}
                  placeholder="Enter state"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="zipCode">Zip/Postal Code *</label>
                <input
                  type="text"
                  id="zipCode"
                  name="zipCode"
                  value={form.zipCode}
                  onChange={handleChange}
                  maxLength={MAX_ZIP_LENGTH}
                  placeholder="Enter zip code"
                  className={errors.zipCode ? 'error' : ''}
                />
                {errors.zipCode && <span className="error-text">{errors.zipCode}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="country">Country</label>
                <select
                  id="country"
                  name="country"
                  value={form.country}
                  onChange={handleChange}
                >
                  <option value="">Select country</option>
                  <option value="US">United States</option>
                  <option value="CA">Canada</option>
                  <option value="UK">United Kingdom</option>
                  <option value="AU">Australia</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="form-section protected-section">
            <h3>Protected Attributes</h3>
            <p className="section-note">This information is used for scholarship eligibility and support services.</p>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="gender">Gender *</label>
                <select
                  id="gender"
                  name="gender"
                  value={form.gender}
                  onChange={handleChange}
                  className={errors.gender ? 'error' : ''}
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="non-binary">Non-binary</option>
                  <option value="prefer-not-to-say">Prefer not to say</option>
                </select>
                {errors.gender && <span className="error-text">{errors.gender}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="race">Race *</label>
                <select
                  id="race"
                  name="race"
                  value={form.race}
                  onChange={handleChange}
                  className={errors.race ? 'error' : ''}
                >
                  <option value="">Select race</option>
                  <option value="american-indian">American Indian or Alaska Native</option>
                  <option value="asian">Asian</option>
                  <option value="black">Black or African American</option>
                  <option value="native-hawaiian">Native Hawaiian or Pacific Islander</option>
                  <option value="white">White</option>
                  <option value="two-or-more">Two or More Races</option>
                  <option value="prefer-not-to-say">Prefer not to say</option>
                </select>
                {errors.race && <span className="error-text">{errors.race}</span>}
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="ethnicity">Ethnicity *</label>
                <select
                  id="ethnicity"
                  name="ethnicity"
                  value={form.ethnicity}
                  onChange={handleChange}
                  className={errors.ethnicity ? 'error' : ''}
                >
                  <option value="">Select ethnicity</option>
                  <option value="hispanic">Hispanic or Latino</option>
                  <option value="not-hispanic">Not Hispanic or Latino</option>
                  <option value="prefer-not-to-say">Prefer not to say</option>
                </select>
                {errors.ethnicity && <span className="error-text">{errors.ethnicity}</span>}
              </div>
              
              <div className="form-group">
                <label htmlFor="educationLevel">Education Level</label>
                <select
                  id="educationLevel"
                  name="educationLevel"
                  value={form.educationLevel}
                  onChange={handleChange}
                >
                  <option value="">Select education level</option>
                  <option value="high-school">High School</option>
                  <option value="associate">Associate Degree</option>
                  <option value="bachelor">Bachelor's Degree</option>
                  <option value="master">Master's Degree</option>
                  <option value="doctorate">Doctorate</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="form-section terms-section">
            <div className="terms-checkbox">
              <input
                type="checkbox"
                id="termsAccepted"
                name="termsAccepted"
                checked={form.termsAccepted}
                onChange={handleChange}
              />
              <label htmlFor="termsAccepted" className="terms-label">
                I understand that my data will be used for training our machine learning models to improve enrollment decisions and student support services.
              </label>
            </div>
            <p className="terms-note">(Optional - checking this box is not required to submit)</p>
          </div>
          
          {errors.submit && (
            <div className="submit-error">{errors.submit}</div>
          )}
          
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? 'Processing...' : 'Submit Enrollment'}
          </button>
        </form>
      </div>
      
      <style jsx>{`
        .enrollment-container {
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        .enrollment-form-card, .enrollment-result-card {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        h1 {
          margin-bottom: 0.5rem;
          color: #1a1a2e;
        }
        
        .form-subtitle {
          color: #666;
          margin-bottom: 2rem;
        }
        
        .form-section {
          margin-bottom: 2rem;
          padding-bottom: 1.5rem;
          border-bottom: 1px solid #eee;
        }
        
        .form-section h3 {
          margin-bottom: 1rem;
          color: #333;
        }
        
        .section-note {
          font-size: 0.875rem;
          color: #666;
          margin-bottom: 1rem;
        }
        
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }
        
        .form-group {
          margin-bottom: 1rem;
          position: relative;
        }
        
        label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
          color: #333;
        }
        
        input, select {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 1rem;
        }
        
        input.error, select.error {
          border-color: #e74c3c;
        }
        
        .char-count {
          position: absolute;
          right: 0.5rem;
          bottom: 0.5rem;
          font-size: 0.75rem;
          color: #999;
        }
        
        .error-text {
          color: #e74c3c;
          font-size: 0.875rem;
        }
        
        .protected-section {
          background: #f8f9fa;
          padding: 1rem;
          border-radius: 8px;
          border: 1px solid #e9ecef;
        }
        
        .terms-section {
          border-bottom: none;
        }
        
        .terms-checkbox {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
        }
        
        .terms-checkbox input {
          width: auto;
          margin-top: 0.25rem;
        }
        
        .terms-label {
          font-weight: normal;
          color: #555;
          line-height: 1.5;
        }
        
        .terms-note {
          font-size: 0.75rem;
          color: #999;
          margin-top: 0.5rem;
          margin-left: 1.75rem;
        }
        
        .submit-error {
          background: #fee;
          color: #c00;
          padding: 0.75rem;
          border-radius: 6px;
          margin-bottom: 1rem;
        }
        
        .btn-submit {
          width: 100%;
          padding: 1rem;
          background: #4f46e5;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
        }
        
        .btn-submit:hover {
          background: #4338ca;
        }
        
        .btn-submit:disabled {
          background: #999;
          cursor: not-allowed;
        }
        
        .decision-status {
          font-size: 1.5rem;
          font-weight: bold;
          padding: 1rem;
          border-radius: 8px;
          text-align: center;
          margin: 1.5rem 0;
        }
        
        .decision-status.approved {
          background: #d4edda;
          color: #155724;
        }
        
        .decision-status.pending {
          background: #fff3cd;
          color: #856404;
        }
        
        .decision-status.rejected {
          background: #f8d7da;
          color: #721c24;
        }
        
        .decision-details {
          background: #f8f9fa;
          padding: 1.5rem;
          border-radius: 8px;
          margin: 1.5rem 0;
        }
        
        .scholarship-notice {
          background: #e7f3ff;
          padding: 1rem;
          border-radius: 6px;
          margin-top: 1rem;
        }
        
        .risk-notice {
          background: #fff3e0;
          padding: 1rem;
          border-radius: 6px;
          margin-top: 1rem;
        }
        
        .enrollment-id {
          color: #666;
          font-size: 0.875rem;
          margin: 1rem 0;
        }
        
        .btn-primary {
          padding: 0.75rem 1.5rem;
          background: #4f46e5;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
        }
        
        @media (max-width: 600px) {
          .form-row {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  )
}
