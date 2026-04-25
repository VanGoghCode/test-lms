'use client'

import { useEffect, useMemo, useState } from 'react'

interface Course {
  id: number
  title: string
  description: string
  instructor: { id: number; name: string; avatar: string }
  category: string
  level: 'beginner' | 'intermediate' | 'advanced'
  thumbnail: string
  duration: string
  modules: Array<{ id: number }>
  average_rating: number
  rating_count: number
}

interface PopularSearch {
  term: string
  count: number
}

function renderStars(value: number): string {
  const rounded = Math.round(value)
  return `${'★'.repeat(rounded)}${'☆'.repeat(5 - rounded)}`
}

export default function Courses() {
  const [courses, setCourses] = useState<Course[]>([])
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [duration, setDuration] = useState('')
  const [level, setLevel] = useState('')
  const [minRating, setMinRating] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [popularSearches, setPopularSearches] = useState<PopularSearch[]>([])
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${baseUrl}/api/courses/search/popular?limit=6`)
      .then((response) => response.json())
      .then((data: { items?: PopularSearch[] }) => setPopularSearches(data.items || []))
      .catch(() => setPopularSearches([]))
  }, [baseUrl])

  useEffect(() => {
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (search) params.set('search', search)
    if (duration) params.set('duration', duration)
    if (level) params.set('level', level)
    if (minRating) params.set('min_rating', minRating)
    
    fetch(`${baseUrl}/api/courses?${params.toString()}`)
      .then((r) => r.json())
      .then(setCourses)
  }, [baseUrl, category, duration, level, minRating, search])

  useEffect(() => {
    const normalizedSearch = search.trim()
    if (!normalizedSearch) {
      setSuggestions([])
      return
    }

    const handle = window.setTimeout(() => {
      fetch(`${baseUrl}/api/courses/search/suggestions?query=${encodeURIComponent(normalizedSearch)}&limit=6`)
        .then((response) => response.json())
        .then((data: { items?: string[] }) => setSuggestions(data.items || []))
        .catch(() => setSuggestions([]))
    }, 250)

    return () => window.clearTimeout(handle)
  }, [baseUrl, search])

  const categories = ['Programming', 'Design', 'Data Science']
  const activeAdvancedFilters = useMemo(
    () => [duration, level, minRating].filter((item) => Boolean(item)).length,
    [duration, level, minRating]
  )

  const applySearch = (term: string) => {
    setSearch(term)
    setShowSuggestions(false)
  }

  return (
    <>
      <h1>Courses</h1>
      <p className="subtitle">Explore our course catalog</p>

      <div className="filters">
        <button 
          className={`filter-btn ${!category ? 'active' : ''}`}
          onClick={() => setCategory('')}
        >
          All
        </button>
        {categories.map(cat => (
          <button
            key={cat}
            className={`filter-btn ${category === cat ? 'active' : ''}`}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="search-wrap" style={{ marginBottom: 16 }}>
        <input
          type="text"
          className="search-input"
          placeholder="Search by title, topic, module, lesson, or instructor"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value)
            setShowSuggestions(true)
          }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => {
            window.setTimeout(() => setShowSuggestions(false), 120)
          }}
        />
        {showSuggestions && suggestions.length > 0 && (
          <div className="suggestions-list" role="listbox" aria-label="Search suggestions">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="suggestion-item"
                onClick={() => applySearch(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      {popularSearches.length > 0 && (
        <div className="popular-searches" style={{ marginBottom: 24 }}>
          <span>Popular:</span>
          {popularSearches.map((item) => (
            <button key={item.term} type="button" className="chip-button" onClick={() => applySearch(item.term)}>
              {item.term}
            </button>
          ))}
        </div>
      )}

      <div className="filter-grid" style={{ marginBottom: 24 }}>
        <select className="select-input" value={duration} onChange={(event) => setDuration(event.target.value)}>
          <option value="">Duration: Any</option>
          <option value="short">Short (&lt; 10 hours)</option>
          <option value="medium">Medium (10-15 hours)</option>
          <option value="long">Long (&gt; 15 hours)</option>
        </select>

        <select className="select-input" value={level} onChange={(event) => setLevel(event.target.value)}>
          <option value="">Level: Any</option>
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>

        <select className="select-input" value={minRating} onChange={(event) => setMinRating(event.target.value)}>
          <option value="">Rating: Any</option>
          <option value="3">3 stars and up</option>
          <option value="4">4 stars and up</option>
          <option value="4.5">4.5 stars and up</option>
        </select>
      </div>

      {activeAdvancedFilters > 0 && (
        <p className="subtitle" style={{ marginBottom: 16 }}>
          {activeAdvancedFilters} advanced filter{activeAdvancedFilters > 1 ? 's' : ''} active
        </p>
      )}

      <div className="grid" style={{ marginTop: 24 }}>
        {courses.map(course => (
          <a href={`/courses/${course.id}`} key={course.id} className="card">
            <div className="card-thumbnail" style={{ background: course.thumbnail }}>
              {course.title.charAt(0)}
            </div>
            <div className="card-body">
              <h3 className="card-title">{course.title}</h3>
              <p className="card-meta">{course.instructor.name} • {course.duration}</p>
              <p className="card-rating" aria-label={`Average rating ${course.average_rating} out of 5`}>
                <span className="stars">{renderStars(course.average_rating)}</span>
                <span>{course.average_rating.toFixed(1)} ({course.rating_count} review{course.rating_count === 1 ? '' : 's'})</span>
              </p>
              <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <span className="badge badge-success">{course.category}</span>
                <span className="badge badge-warning">{course.level}</span>
              </div>
            </div>
          </a>
        ))}
      </div>

      {courses.length === 0 && (
        <p className="subtitle" style={{ marginTop: 24 }}>
          No courses match your current search and filters.
        </p>
      )}
    </>
  )
}