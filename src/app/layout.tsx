import './globals.css'
import type { Metadata } from 'next'
import { AuthProvider } from './auth-context'
import { Header } from './header'

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
        <AuthProvider>
          <Header />
          <main className="container">
            {children}
          </main>
          <footer className="footer">
            <div className="container">
              © 2024 Minimalist LMS. All rights reserved.
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  )
}