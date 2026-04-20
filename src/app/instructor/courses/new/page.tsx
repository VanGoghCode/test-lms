'use client'
import { useAuth } from '../../../auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

interface Module {
  title: string
  lessons: { title: string; duration: string; video_url: string }[]
}

type LessonField = keyof Module['lessons'][number]

const CATEGORIES = ['Programming', 'Design', 'Data Science', 'Business', 'Marketing']
const THUMBNAILS = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
  'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
]

export default function NewCourse() {
  const { user, token, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState(CATEGORIES[0])
  const [thumbnail, setThumbnail] = useState(THUMBNAILS[0])
  const [duration, setDuration] = useState('')
  const [modules, setModules] = useState<Module[]>([{ title: '', lessons: [{ title: '', duration: '', video_url: '' }] }])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (authLoading) return
    if (!user || !token) {
      router.push('/login')
      return
    }
    if (user.role !== 'instructor' && user.role !== 'admin') {
      router.push('/')
    }
  }, [user, token, authLoading, router])

  const addModule = () => {
    setModules([...modules, { title: '', lessons: [{ title: '', duration: '', video_url: '' }] }])
  }

  const updateModule = (idx: number, title: string) => {
    const updated = [...modules]
    updated[idx].title = title
    setModules(updated)
  }

  const addLesson = (moduleIdx: number) => {
    const updated = [...modules]
    updated[moduleIdx].lessons.push({ title: '', duration: '', video_url: '' })
    setModules(updated)
  }

  const updateLesson = (moduleIdx: number, lessonIdx: number, field: LessonField, value: string) => {
    const updated = [...modules]
    updated[moduleIdx].lessons[lessonIdx][field] = value
    setModules(updated)
  }

  const removeLesson = (moduleIdx: number, lessonIdx: number) => {
    const updated = [...modules]
    updated[moduleIdx].lessons.splice(lessonIdx, 1)
    setModules(updated)
  }

  const removeModule = (idx: number) => {
    setModules(modules.filter((_, i) => i !== idx))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      const courseData = {
        title,
        description,
        category,
        thumbnail,
        duration: duration || '0 hours',
        modules: modules.filter(m => m.title).map(m => ({
          title: m.title,
          lessons: m.lessons.filter(l => l.title).map(l => ({
            title: l.title,
            duration: l.duration || '0 min',
            video_url: l.video_url || null
          }))
        }))
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/courses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(courseData)
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to create course')
      }

      router.push('/instructor')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (authLoading) return <div className="container"><p>Loading...</p></div>

  return (
    <div className="course-editor">
      <h1>Create New Course</h1>
      <p className="subtitle">Fill in the details to create your course</p>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <h2>Basic Information</h2>
          
          <div className="form-group">
            <label>Course Title</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
              placeholder="e.g., Python for Beginners"
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              required
              rows={4}
              placeholder="Describe what students will learn..."
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Category</label>
              <select value={category} onChange={e => setCategory(e.target.value)}>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label>Duration</label>
              <input
                type="text"
                value={duration}
                onChange={e => setDuration(e.target.value)}
                placeholder="e.g., 10 hours"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Thumbnail</label>
            <div className="thumbnail-grid">
              {THUMBNAILS.map((t, i) => (
                <div
                  key={i}
                  className={`thumbnail-option ${thumbnail === t ? 'selected' : ''}`}
                  style={{ background: t }}
                  onClick={() => setThumbnail(t)}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="form-section">
          <h2>Course Content</h2>
          
          {modules.map((module, moduleIdx) => (
            <div key={moduleIdx} className="module-editor">
              <div className="module-header-row">
                <div className="form-group" style={{ flex: 1 }}>
                  <label>Module {moduleIdx + 1} Title</label>
                  <input
                    type="text"
                    value={module.title}
                    onChange={e => updateModule(moduleIdx, e.target.value)}
                    placeholder="e.g., Getting Started"
                  />
                </div>
                {modules.length > 1 && (
                  <button type="button" onClick={() => removeModule(moduleIdx)} className="btn-remove">×</button>
                )}
              </div>

              <div className="lessons-list">
                {module.lessons.map((lesson, lessonIdx) => (
                  <div key={lessonIdx} className="lesson-editor">
                    <div className="form-row">
                      <div className="form-group" style={{ flex: 2 }}>
                        <label>Lesson {lessonIdx + 1}</label>
                        <input
                          type="text"
                          value={lesson.title}
                          onChange={e => updateLesson(moduleIdx, lessonIdx, 'title', e.target.value)}
                          placeholder="Lesson title"
                        />
                      </div>
                      <div className="form-group">
                        <label>Duration</label>
                        <input
                          type="text"
                          value={lesson.duration}
                          onChange={e => updateLesson(moduleIdx, lessonIdx, 'duration', e.target.value)}
                          placeholder="e.g., 15 min"
                        />
                      </div>
                      <div className="form-group" style={{ flex: 2 }}>
                        <label>Video URL (optional)</label>
                        <input
                          type="url"
                          value={lesson.video_url}
                          onChange={e => updateLesson(moduleIdx, lessonIdx, 'video_url', e.target.value)}
                          placeholder="https://..."
                        />
                      </div>
                      {module.lessons.length > 1 && (
                        <button type="button" onClick={() => removeLesson(moduleIdx, lessonIdx)} className="btn-remove">×</button>
                      )}
                    </div>
                  </div>
                ))}
                <button type="button" onClick={() => addLesson(moduleIdx)} className="btn-add-lesson">+ Add Lesson</button>
              </div>
            </div>
          ))}
          
          <button type="button" onClick={addModule} className="btn-add-module">+ Add Module</button>
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => router.back()} className="btn-secondary">Cancel</button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Creating...' : 'Create Course'}
          </button>
        </div>
      </form>
    </div>
  )
}