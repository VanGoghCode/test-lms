import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Minimalist LMS',
  description: 'A simple learning management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <header className="header">
          <div className="container header-content">
            <a href="/" className="logo">LMS</a>
            <nav className="nav">
              <a href="/courses">Courses</a>
              <a href="/my-learning">My Learning</a>
              <a href="/assignments">Assignments</a>
            </nav>
            <div className="user-avatar">AR</div>
          </div>
        </header>
        <main className="container">
          {children}
        </main>
        <footer className="footer">
          <div className="container">
            © 2024 Minimalist LMS. All rights reserved.
          </div>
        </footer>
      </body>
    </html>
  )
}