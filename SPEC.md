# Learning Management System (LMS) - Specification

## Project Overview
- **Project Name**: Minimalist LMS
- **Type**: Full-stack web application
- **Core Functionality**: A simple learning management system with course browsing, student enrollment, assignment tracking, and progress monitoring
- **Target Users**: Students and instructors

## Tech Stack
- Frontend: Next.js 14 (App Router), TypeScript
- Backend: Python FastAPI
- Styling: CSS Modules

## UI/UX Specification

### Layout Structure
- **Header**: Logo, navigation (Courses, My Learning, Assignments), user avatar
- **Main Content**: Dynamic based on route
- **Sidebar** (on relevant pages): Quick links, notifications
- **Footer**: Minimal copyright

### Responsive Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Visual Design

#### Color Palette
- Background: `#0D0D0D` (near black)
- Surface: `#1A1A1A` (dark gray)
- Surface Elevated: `#252525`
- Primary: `#E8C547` (warm gold)
- Primary Hover: `#F5D76E`
- Text Primary: `#F5F5F5`
- Text Secondary: `#A0A0A0`
- Border: `#333333`
- Success: `#4ADE80`
- Error: `#F87171`

#### Typography
- Font Family: `"DM Sans", sans-serif`
- Headings: 700 weight
  - H1: 2.5rem
  - H2: 1.75rem
  - H3: 1.25rem
- Body: 400 weight, 1rem
- Small: 0.875rem

#### Spacing System
- Base unit: 8px
- xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, 2xl: 48px

#### Visual Effects
- Border radius: 8px (cards), 4px (buttons), 50% (avatars)
- Box shadow: `0 4px 20px rgba(0,0,0,0.3)`
- Transitions: 200ms ease

### Components

#### Course Card
- Thumbnail placeholder (gradient)
- Title, instructor name
- Progress bar (if enrolled)
- Enrollment status badge

#### Assignment Card
- Title, due date
- Status (pending/submitted/graded)
- Grade display (if graded)

#### User Avatar
- Circular, 40px default
- Initials fallback

#### Button
- Primary: Gold background, dark text
- Secondary: Transparent with border
- States: hover (brightness), disabled (opacity 0.5)

## Functionality Specification

### Pages

1. **Home** (`/`)
   - Welcome message with user name
   - Quick stats (enrolled courses, pending assignments)
   - Recent activity

2. **Courses** (`/courses`)
   - Grid of course cards
   - Filter by category
   - Search by title

3. **Course Detail** (`/courses/[id]`)
   - Course info, description
   - Module/lesson list
   - Enroll button (if not enrolled)
   - Continue button (if enrolled)

4. **My Learning** (`/my-learning`)
   - Enrolled courses with progress
   - Continue learning CTA

5. **Assignments** (`/assignments`)
   - List of assignments
   - Filter by status
   - Due date display

### API Endpoints (Python FastAPI)

- `GET /api/courses` - List all courses
- `GET /api/courses/[id]` - Get course details
- `GET /api/users/[id]/enrollments` - Get user enrollments
- `GET /api/users/[id]/assignments` - Get user assignments
- `POST /api/courses/[id]/enroll` - Enroll in course

### Mock Data
- 6 courses across 3 categories (Programming, Design, Data Science)
- 3 students, 2 instructors
- 10 assignments with various statuses

## Acceptance Criteria
- [ ] Home page loads with user stats
- [ ] Courses page displays all courses in grid
- [ ] Course detail shows full course info
- [ ] Can navigate between all pages
- [ ] Responsive on mobile/tablet/desktop
- [ ] API returns mock data correctly
- [ ] Dark theme applied consistently