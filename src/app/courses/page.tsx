'use client'

import { useState, useEffect } from 'react'

interface Course {
  id: number
  title: string
  description: string
  instructor: { id: number; name: string; avatar: string }
  category: string
  thumbnail: string
  duration: string
  modules: any[]
}

export default function Courses() {
  const [courses, setCourses] = useState<Course[]>([])
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (search) params.set('search', search)
    
    fetch(`http://localhost:8000/api/courses?${params}`)
      .then(r => r.json())
      .then(setCourses)
  }, [category, search])

  const categories = ['Programming', 'Design', 'Data Science']

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

      <input
        type="text"
        className="search-input"
        placeholder="Search courses..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      <div className="grid" style={{ marginTop: 24 }}>
        {courses.map(course => (
          <a href={`/courses/${course.id}`} key={course.id} className="card">
            <div className="card-thumbnail" style={{ background: course.thumbnail }}>
              {course.title.charAt(0)}
            </div>
            <div className="card-body">
              <h3 className="card-title">{course.title}</h3>
              <p className="card-meta">{course.instructor.name} • {course.duration}</p>
              <span className="badge badge-success" style={{ marginTop: 8 }}>{course.category}</span>
            </div>
          </a>
        ))}
      </div>
    </>
  )
}