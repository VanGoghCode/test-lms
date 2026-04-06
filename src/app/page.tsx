async function getData() {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const [enrollments, assignments] = await Promise.all([
    fetch(`${baseUrl}/api/users/1/enrollments`, { cache: 'no-store' }).then(r => r.json()),
    fetch(`${baseUrl}/api/users/1/assignments`, { cache: 'no-store' }).then(r => r.json()),
  ])
  return { enrollments, assignments }
}

export default async function Home() {
  const { enrollments, assignments } = await getData()
  const pendingAssignments = assignments.filter((a: any) => a.status === 'pending').length

  return (
    <>
      <h1>Welcome back, Alex</h1>
      <p className="subtitle">Continue your learning journey</p>

      <div className="stats">
        <div className="stat-card">
          <div className="stat-value">{enrollments.length}</div>
          <div className="stat-label">Enrolled Courses</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{pendingAssignments}</div>
          <div className="stat-label">Pending Assignments</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {Math.round(enrollments.reduce((acc: number, e: any) => acc + e.progress, 0) / enrollments.length || 0)}%
          </div>
          <div className="stat-label">Average Progress</div>
        </div>
      </div>

      <h2>Continue Learning</h2>
      <div className="grid">
        {enrollments.slice(0, 3).map((enrollment: any) => (
          <a href={`/courses/${enrollment.course_id}`} key={enrollment.id} className="card">
            <div className="card-thumbnail" style={{ background: enrollment.course.thumbnail }}>
              {enrollment.course.title.charAt(0)}
            </div>
            <div className="card-body">
              <h3 className="card-title">{enrollment.course.title}</h3>
              <p className="card-meta">{enrollment.course.instructor.name}</p>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${enrollment.progress}%` }} />
              </div>
            </div>
          </a>
        ))}
      </div>
    </>
  )
}