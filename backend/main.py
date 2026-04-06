from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from enum import Enum

app = FastAPI()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

class Role(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"

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
    video_url: Optional[str] = None

class Module(BaseModel):
    id: int
    title: str
    lessons: List[Lesson]

class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

class Course(BaseModel):
    id: int
    title: str
    description: str
    instructor: Instructor
    category: str
    thumbnail: str
    duration: str
    modules: List[Module]
    status: CourseStatus = CourseStatus.DRAFT

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

# Auth Models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Role = Role.STUDENT

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Auth helpers
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(user_id: int, email: str, role: Role) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role.value,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# In-memory user store (replace with database in production)
users_db: dict[int, dict] = {}
user_by_email: dict[str, dict] = {}

# Seed default users
default_users = [
    {"id": 1, "name": "Alex Rivera", "email": "alex@example.com", "password": get_password_hash("password123"), "role": Role.STUDENT, "avatar": "AR"},
    {"id": 2, "name": "Jordan Lee", "email": "jordan@example.com", "password": get_password_hash("password123"), "role": Role.INSTRUCTOR, "avatar": "JL"},
    {"id": 3, "name": "Casey Morgan", "email": "casey@example.com", "password": get_password_hash("password123"), "role": Role.ADMIN, "avatar": "CM"},
]
for u in default_users:
    users_db[u["id"]] = u
    user_by_email[u["email"]] = u

# Auth dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    user = users_db.get(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(*allowed_roles: Role):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if Role(current_user["role"]) not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Auth endpoints
@app.post("/api/auth/register", response_model=Token)
def register(user_data: UserCreate):
    if user_data.email in user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = len(users_db) + 1
    new_user = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": get_password_hash(user_data.password),
        "role": user_data.role,
        "avatar": "".join(w[0] for w in user_data.name.split()[:2]).upper()
    }
    users_db[user_id] = new_user
    user_by_email[user_data.email] = new_user
    
    token = create_token(user_id, user_data.email, user_data.role)
    return {"access_token": token, "token_type": "bearer", "user": new_user}

@app.post("/api/auth/login", response_model=Token)
def login(credentials: UserLogin):
    user = user_by_email.get(credentials.email)
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"], user["email"], user["role"])
    return {"access_token": token, "token_type": "bearer", "user": user}

@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# Course Management Models
class LessonCreate(BaseModel):
    title: str
    duration: str
    video_url: Optional[str] = None

class ModuleCreate(BaseModel):
    title: str
    lessons: List[LessonCreate] = []

class CourseCreate(BaseModel):
    title: str
    description: str
    category: str
    thumbnail: str
    duration: str
    modules: List[ModuleCreate] = []

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[str] = None
    modules: Optional[List[ModuleCreate]] = None

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

# Instructor Course Management
@app.post("/api/courses", status_code=201)
def create_course(course_data: CourseCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course_id = len(courses) + 1
    
    # Convert module/lesson creation to proper objects
    modules = []
    for m_idx, m in enumerate(course_data.modules):
        lessons = []
        for l_idx, l in enumerate(m.lessons):
            lessons.append(Lesson(
                id=m_idx * 100 + l_idx + 1,
                title=l.title,
                duration=l.duration,
                video_url=l.video_url
            ))
        modules.append(Module(
            id=m_idx + 1,
            title=m.title,
            lessons=lessons
        ))
    
    new_course = Course(
        id=course_id,
        title=course_data.title,
        description=course_data.description,
        instructor=Instructor(id=current_user["id"], name=current_user["name"], avatar=current_user["avatar"]),
        category=course_data.category,
        thumbnail=course_data.thumbnail,
        duration=course_data.duration,
        modules=modules,
        status=CourseStatus.DRAFT
    )
    courses.append(new_course)
    return new_course

@app.put("/api/courses/{course_id}")
def update_course(course_id: int, course_data: CourseUpdate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check ownership for instructors (admins can edit any)
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")
    
    if course_data.title is not None:
        course.title = course_data.title
    if course_data.description is not None:
        course.description = course_data.description
    if course_data.category is not None:
        course.category = course_data.category
    if course_data.thumbnail is not None:
        course.thumbnail = course_data.thumbnail
    if course_data.duration is not None:
        course.duration = course_data.duration
    if course_data.modules is not None:
        modules = []
        for m_idx, m in enumerate(course_data.modules):
            lessons = []
            for l_idx, l in enumerate(m.lessons):
                lessons.append(Lesson(
                    id=m_idx * 100 + l_idx + 1,
                    title=l.title,
                    duration=l.duration,
                    video_url=l.video_url
                ))
            modules.append(Module(id=m_idx + 1, title=m.title, lessons=lessons))
        course.modules = modules
    
    return course

@app.delete("/api/courses/{course_id}")
def delete_course(course_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this course")
    
    courses.remove(course)
    return {"message": "Course deleted"}

@app.post("/api/courses/{course_id}/publish")
def publish_course(course_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to publish this course")
    
    course.status = CourseStatus.PUBLISHED
    return course

@app.post("/api/courses/{course_id}/unpublish")
def unpublish_course(course_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to unpublish this course")
    
    course.status = CourseStatus.DRAFT
    return course

# Module CRUD
@app.post("/api/courses/{course_id}/modules")
def add_module(course_id: int, module: ModuleCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")
    
    module_id = len(course.modules) + 1
    lessons = [
        Lesson(id=module_id * 100 + i + 1, title=l.title, duration=l.duration, video_url=l.video_url)
        for i, l in enumerate(module.lessons)
    ]
    new_module = Module(id=module_id, title=module.title, lessons=lessons)
    course.modules.append(new_module)
    return new_module

@app.put("/api/courses/{course_id}/modules/{module_id}")
def update_module(course_id: int, module_id: int, module: ModuleCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")
    
    existing_module = next((m for m in course.modules if m.id == module_id), None)
    if not existing_module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    lessons = [
        Lesson(id=module_id * 100 + i + 1, title=l.title, duration=l.duration, video_url=l.video_url)
        for i, l in enumerate(module.lessons)
    ]
    existing_module.title = module.title
    existing_module.lessons = lessons
    return existing_module

@app.delete("/api/courses/{course_id}/modules/{module_id}")
def delete_module(course_id: int, module_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")
    
    module = next((m for m in course.modules if m.id == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    course.modules.remove(module)
    return {"message": "Module deleted"}

# Lesson CRUD
@app.post("/api/courses/{course_id}/modules/{module_id}/lessons")
def add_lesson(course_id: int, module_id: int, lesson: LessonCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")
    
    module = next((m for m in course.modules if m.id == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    lesson_id = len(module.lessons) + 1
    new_lesson = Lesson(id=lesson_id, title=lesson.title, duration=lesson.duration, video_url=lesson.video_url)
    module.lessons.append(new_lesson)
    return new_lesson

@app.put("/api/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}")
def update_lesson(course_id: int, module_id: int, lesson_id: int, lesson: LessonCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")
    
    module = next((m for m in course.modules if m.id == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    existing_lesson = next((l for l in module.lessons if l.id == lesson_id), None)
    if not existing_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    existing_lesson.title = lesson.title
    existing_lesson.duration = lesson.duration
    existing_lesson.video_url = lesson.video_url
    return existing_lesson

@app.delete("/api/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}")
def delete_lesson(course_id: int, module_id: int, lesson_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if current_user["role"] != Role.ADMIN and course.instructor.id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this course")
    
    module = next((m for m in course.modules if m.id == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    lesson = next((l for l in module.lessons if l.id == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    module.lessons.remove(lesson)
    return {"message": "Lesson deleted"}

# Get instructor's courses
@app.get("/api/instructor/courses")
def get_instructor_courses(current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    return [c for c in courses if c.instructor.id == current_user["id"]]

@app.get("/api/users/{user_id}/enrollments")
def get_enrollments(user_id: int, current_user: dict = Depends(get_current_user)):
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