from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Instructor(BaseModel):
    id: int
    name: str
    avatar: str

class Lesson(BaseModel):
    id: int
    title: str
    duration: str

class Module(BaseModel):
    id: int
    title: str
    lessons: List[Lesson]

class Course(BaseModel):
    id: int
    title: str
    description: str
    instructor: Instructor
    category: str
    thumbnail: str
    duration: str
    modules: List[Module]

class Enrollment(BaseModel):
    id: int
    course_id: int
    user_id: int
    progress: int
    enrolled_at: str

class Assignment(BaseModel):
    id: int
    title: str
    course_id: int
    course_name: str
    due_date: str
    status: str
    grade: Optional[int] = None

class User(BaseModel):
    id: int
    name: str
    email: str
    avatar: str

# Mock Data
instructors = [
    Instructor(id=1, name="Sarah Chen", avatar="SC"),
    Instructor(id=2, name="Marcus Johnson", avatar="MJ"),
]

courses = [
    Course(
        id=1,
        title="Python Fundamentals",
        description="Learn Python from scratch. This course covers variables, data types, control flow, functions, and basic object-oriented programming concepts.",
        instructor=instructors[0],
        category="Programming",
        thumbnail="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        duration="12 hours",
        modules=[
            Module(id=1, title="Getting Started", lessons=[
                Lesson(id=1, title="Introduction to Python", duration="15 min"),
                Lesson(id=2, title="Setting Up Your Environment", duration="20 min"),
            ]),
            Module(id=2, title="Basic Syntax", lessons=[
                Lesson(id=3, title="Variables and Data Types", duration="25 min"),
                Lesson(id=4, title="Operators", duration="20 min"),
            ]),
        ]
    ),
    Course(
        id=2,
        title="JavaScript Essentials",
        description="Master JavaScript programming. From variables and functions to DOM manipulation and async programming.",
        instructor=instructors[1],
        category="Programming",
        thumbnail="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        duration="15 hours",
        modules=[
            Module(id=1, title="Core Concepts", lessons=[
                Lesson(id=1, title="Variables and Scope", duration="20 min"),
                Lesson(id=2, title="Functions", duration="30 min"),
            ]),
        ]
    ),
    Course(
        id=3,
        title="UI Design Principles",
        description="Learn the fundamentals of user interface design. Master typography, color theory, layout, and design systems.",
        instructor=instructors[0],
        category="Design",
        thumbnail="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        duration="8 hours",
        modules=[
            Module(id=1, title="Design Foundations", lessons=[
                Lesson(id=1, title="Typography Basics", duration="25 min"),
                Lesson(id=2, title="Color Theory", duration="30 min"),
            ]),
        ]
    ),
    Course(
        id=4,
        title="Figma Masterclass",
        description="Become proficient in Figma. Learn components, auto-layout, prototyping, and design systems.",
        instructor=instructors[1],
        category="Design",
        thumbnail="linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        duration="10 hours",
        modules=[
            Module(id=1, title="Figma Basics", lessons=[
                Lesson(id=1, title="Interface Overview", duration="15 min"),
                Lesson(id=2, title="Working with Frames", duration="25 min"),
            ]),
        ]
    ),
    Course(
        id=5,
        title="Data Science with Python",
        description="Analyze data using Python. Cover NumPy, Pandas, visualization with Matplotlib, and basic machine learning.",
        instructor=instructors[0],
        category="Data Science",
        thumbnail="linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
        duration="20 hours",
        modules=[
            Module(id=1, title="Data Analysis", lessons=[
                Lesson(id=1, title="NumPy Basics", duration="30 min"),
                Lesson(id=2, title="Pandas DataFrames", duration="45 min"),
            ]),
        ]
    ),
    Course(
        id=6,
        title="Machine Learning Intro",
        description="Introduction to machine learning concepts. Learn regression, classification, and neural network basics.",
        instructor=instructors[1],
        category="Data Science",
        thumbnail="linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        duration="18 hours",
        modules=[
            Module(id=1, title="ML Foundations", lessons=[
                Lesson(id=1, title="What is ML?", duration="20 min"),
                Lesson(id=2, title="Linear Regression", duration="35 min"),
            ]),
        ]
    ),
]

users = [
    User(id=1, name="Alex Rivera", email="alex@example.com", avatar="AR"),
    User(id=2, name="Jordan Lee", email="jordan@example.com", avatar="JL"),
    User(id=3, name="Casey Morgan", email="casey@example.com", avatar="CM"),
]

enrollments = [
    Enrollment(id=1, course_id=1, user_id=1, progress=65, enrolled_at="2024-01-15"),
    Enrollment(id=2, course_id=3, user_id=1, progress=30, enrolled_at="2024-02-01"),
    Enrollment(id=3, course_id=5, user_id=1, progress=80, enrolled_at="2024-01-20"),
]

assignments = [
    Assignment(id=1, title="Python Basics Quiz", course_id=1, course_name="Python Fundamentals", due_date="2024-03-15", status="graded", grade=92),
    Assignment(id=2, title="Functions Assignment", course_id=1, course_name="Python Fundamentals", due_date="2024-03-20", status="submitted"),
    Assignment(id=3, title="JavaScript Project", course_id=2, course_name="JavaScript Essentials", due_date="2024-03-25", status="pending"),
    Assignment(id=4, title="Design Critique", course_id=3, course_name="UI Design Principles", due_date="2024-03-18", status="graded", grade=88),
    Assignment(id=5, title="Figma Wireframe", course_id=4, course_name="Figma Masterclass", due_date="2024-03-22", status="pending"),
    Assignment(id=6, title="Data Analysis Report", course_id=5, course_name="Data Science with Python", due_date="2024-03-28", status="pending"),
    Assignment(id=7, title="OOP Exercise", course_id=1, course_name="Python Fundamentals", due_date="2024-03-10", status="graded", grade=85),
    Assignment(id=8, title="Color Palette Design", course_id=3, course_name="UI Design Principles", due_date="2024-03-12", status="submitted"),
    Assignment(id=9, title="Pandas Practice", course_id=5, course_name="Data Science with Python", due_date="2024-03-30", status="pending"),
    Assignment(id=10, title="ML Model Building", course_id=6, course_name="Machine Learning Intro", due_date="2024-04-05", status="pending"),
]

# Endpoints
@app.get("/api/courses")
def get_courses(category: str = None, search: str = None):
    result = courses
    if category:
        result = [c for c in result if c.category == category]
    if search:
        result = [c for c in result if search.lower() in c.title.lower()]
    return result

@app.get("/api/courses/{course_id}")
def get_course(course_id: int):
    return next((c for c in courses if c.id == course_id), None)

@app.get("/api/users/{user_id}/enrollments")
def get_enrollments(user_id: int):
    user_enrollments = [e for e in enrollments if e.user_id == user_id]
    result = []
    for e in user_enrollments:
        course = next((c for c in courses if c.id == e.course_id), None)
        if course:
            result.append({**e.dict(), "course": course})
    return result

@app.get("/api/users/{user_id}/assignments")
def get_assignments(user_id: int, status: str = None):
    result = assignments
    if status:
        result = [a for a in result if a.status == status]
    return result

@app.post("/api/courses/{course_id}/enroll")
def enroll_course(course_id: int, user_id: int = 1):
    new_enrollment = Enrollment(
        id=len(enrollments) + 1,
        course_id=course_id,
        user_id=user_id,
        progress=0,
        enrolled_at="2024-03-01"
    )
    enrollments.append(new_enrollment)
    return new_enrollment

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return next((u for u in users if u.id == user_id), None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)