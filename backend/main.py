from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from enum import Enum
import secrets

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

# Progress Tracking Models
class LessonProgress(BaseModel):
    lesson_id: int
    completed: bool = False

class CourseProgress(BaseModel):
    course_id: int
    completed_lessons: List[int] = []

class ProgressUpdate(BaseModel):
    lesson_id: int
    completed: bool

class Assignment(BaseModel):
    id: int
    title: str
    course_id: int
    course_name: str
    description: str
    due_date: str
    status: str
    max_grade: int = 100
    grade: Optional[int] = None
    feedback: Optional[str] = None

# Assignment System Models
class AssignmentCreate(BaseModel):
    title: str
    course_id: int
    description: str
    due_date: str
    max_grade: int = 100

class AssignmentSubmission(BaseModel):
    assignment_id: int
    content: str
    file_url: Optional[str] = None

class GradeSubmission(BaseModel):
    grade: int
    feedback: Optional[str] = None

# Quiz/Exam Models
class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"

class QuizQuestion(BaseModel):
    id: int
    question: str
    type: QuestionType
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str
    points: int = 1

class Quiz(BaseModel):
    id: int
    title: str
    course_id: int
    course_name: str
    description: str
    time_limit: Optional[int] = None  # in minutes
    questions: List[QuizQuestion]
    total_points: int
    passing_score: int

class QuizCreate(BaseModel):
    title: str
    course_id: int
    description: str
    time_limit: Optional[int] = None
    passing_score: int = 70

class QuestionCreate(BaseModel):
    question: str
    type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: str
    points: int = 1

class QuizAnswer(BaseModel):
    question_id: int
    answer: str

class QuizSubmission(BaseModel):
    quiz_id: int
    answers: List[QuizAnswer]

# Discussion Forum Models
class DiscussionPost(BaseModel):
    id: int
    course_id: int
    user_id: int
    user_name: str
    user_avatar: str
    title: str
    content: str
    created_at: str
    upvotes: int = 0
    is_pinned: bool = False
    reply_count: int = 0

class PostCreate(BaseModel):
    course_id: int
    title: str
    content: str

class Reply(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_name: str
    user_avatar: str
    content: str
    created_at: str
    upvotes: int = 0

class ReplyCreate(BaseModel):
    content: str

# Certificate Models
class Certificate(BaseModel):
    id: int
    user_id: int
    user_name: str
    course_id: int
    course_name: str
    instructor_name: str
    issued_at: str
    verification_code: str
    completion_date: str

class CompletionCriteria(BaseModel):
    min_progress: int = 100  # percentage
    required_assignments: bool = False
    required_quizzes: bool = False
    min_quiz_score: int = 70  # percentage

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

# Progress tracking: {user_id: {course_id: [completed_lesson_ids]}}
progress_db: dict[int, dict[int, List[int]]] = {}

assignments = [
    Assignment(id=1, title="Python Basics Quiz", course_id=1, course_name="Python Fundamentals", description="Complete the quiz on Python basics", due_date="2024-03-15", status="graded", grade=92),
    Assignment(id=2, title="Functions Assignment", course_id=1, course_name="Python Fundamentals", description="Write functions to solve the given problems", due_date="2024-03-20", status="submitted"),
    Assignment(id=3, title="JavaScript Project", course_id=2, course_name="JavaScript Essentials", description="Build a simple to-do app", due_date="2024-03-25", status="pending"),
    Assignment(id=4, title="Design Critique", course_id=3, course_name="UI Design Principles", description="Critique the provided design", due_date="2024-03-18", status="graded", grade=88),
    Assignment(id=5, title="Figma Wireframe", course_id=4, course_name="Figma Masterclass", description="Create a wireframe for a mobile app", due_date="2024-03-22", status="pending"),
    Assignment(id=6, title="Data Analysis Report", course_id=5, course_name="Data Science with Python", description="Analyze the provided dataset", due_date="2024-03-28", status="pending"),
    Assignment(id=7, title="OOP Exercise", course_id=1, course_name="Python Fundamentals", description="Implement a class hierarchy", due_date="2024-03-10", status="graded", grade=85),
    Assignment(id=8, title="Color Palette Design", course_id=3, course_name="UI Design Principles", description="Design a color palette", due_date="2024-03-12", status="submitted"),
    Assignment(id=9, title="Pandas Practice", course_id=5, course_name="Data Science with Python", description="Complete pandas exercises", due_date="2024-03-30", status="pending"),
    Assignment(id=10, title="ML Model Building", course_id=6, course_name="Machine Learning Intro", description="Build a simple ML model", due_date="2024-04-05", status="pending"),
]

# Submissions: {assignment_id: [{user_id, content, file_url, submitted_at, is_late}]}
submissions_db: dict[int, list] = {}

# Quiz data
quizzes: List[Quiz] = []

# Quiz attempts: {quiz_id: [{user_id, answers, score, submitted_at, time_taken}]}
quiz_attempts_db: dict[int, list] = {}

# Discussion Forum data
discussion_posts: List[DiscussionPost] = []
post_replies: dict[int, List[Reply]] = {}  # {post_id: [replies]}
post_upvotes: dict[int, List[int]] = {}  # {post_id: [user_ids]}
reply_upvotes: dict[int, List[int]] = {}  # {reply_id: [user_ids]}

# Certificate data
certificates: List[Certificate] = []
course_completion_criteria: dict[int, CompletionCriteria] = {}  # {course_id: criteria}

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

# Progress Tracking Endpoints
@app.get("/api/courses/{course_id}/progress")
def get_course_progress(course_id: int, current_user: dict = Depends(get_current_user)):
    """Get user's progress for a specific course"""
    user_progress = progress_db.get(current_user["id"], {})
    completed_lessons = user_progress.get(course_id, [])
    
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Calculate total lessons
    total_lessons = sum(len(m.lessons) for m in course.modules)
    progress_percent = int((len(completed_lessons) / total_lessons * 100) if total_lessons > 0 else 0)
    
    return {
        "course_id": course_id,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "progress_percent": progress_percent
    }

@app.post("/api/courses/{course_id}/progress")
def update_lesson_progress(course_id: int, progress: ProgressUpdate, current_user: dict = Depends(get_current_user)):
    """Update completion status for a lesson"""
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Verify lesson exists
    lesson_exists = any(
        any(l.id == progress.lesson_id for l in m.lessons)
        for m in course.modules
    )
    if not lesson_exists:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Initialize user progress if needed
    if current_user["id"] not in progress_db:
        progress_db[current_user["id"]] = {}
    if course_id not in progress_db[current_user["id"]]:
        progress_db[current_user["id"]][course_id] = []
    
    user_course_progress = progress_db[current_user["id"]][course_id]
    
    if progress.completed and progress.lesson_id not in user_course_progress:
        user_course_progress.append(progress.lesson_id)
    elif not progress.completed and progress.lesson_id in user_course_progress:
        user_course_progress.remove(progress.lesson_id)
    
    # Recalculate progress percentage
    total_lessons = sum(len(m.lessons) for m in course.modules)
    progress_percent = int((len(user_course_progress) / total_lessons * 100) if total_lessons > 0 else 0)
    
    # Update enrollment progress
    enrollment = next((e for e in enrollments if e.course_id == course_id and e.user_id == current_user["id"]), None)
    if enrollment:
        enrollment.progress = progress_percent
    
    return {
        "course_id": course_id,
        "completed_lessons": user_course_progress,
        "total_lessons": total_lessons,
        "progress_percent": progress_percent
    }

@app.get("/api/users/{user_id}/progress")
def get_user_all_progress(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get all progress for a user"""
    if current_user["id"] != user_id and current_user["role"] != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    user_progress = progress_db.get(user_id, {})
    result = []
    
    for course_id, completed_lessons in user_progress.items():
        course = next((c for c in courses if c.id == course_id), None)
        if course:
            total_lessons = sum(len(m.lessons) for m in course.modules)
            progress_percent = int((len(completed_lessons) / total_lessons * 100) if total_lessons > 0 else 0)
            result.append({
                "course_id": course_id,
                "course_title": course.title,
                "completed_lessons": completed_lessons,
                "total_lessons": total_lessons,
                "progress_percent": progress_percent
            })
    
    return result

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

# Assignment System Endpoints
@app.post("/api/assignments", status_code=201)
def create_assignment(assignment: AssignmentCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Create a new assignment (instructor/admin only)"""
    course = next((c for c in courses if c.id == assignment.course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_assignment = Assignment(
        id=len(assignments) + 1,
        title=assignment.title,
        course_id=assignment.course_id,
        course_name=course.title,
        description=assignment.description,
        due_date=assignment.due_date,
        status="pending",
        max_grade=assignment.max_grade
    )
    assignments.append(new_assignment)
    return new_assignment

@app.get("/api/assignments/{assignment_id}")
def get_assignment(assignment_id: int):
    """Get assignment details"""
    assignment = next((a for a in assignments if a.id == assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@app.put("/api/assignments/{assignment_id}")
def update_assignment(assignment_id: int, assignment: AssignmentCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Update an assignment (instructor/admin only)"""
    existing = next((a for a in assignments if a.id == assignment_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    course = next((c for c in courses if c.id == assignment.course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    existing.title = assignment.title
    existing.course_id = assignment.course_id
    existing.course_name = course.title
    existing.description = assignment.description
    existing.due_date = assignment.due_date
    existing.max_grade = assignment.max_grade
    return existing

@app.delete("/api/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Delete an assignment (instructor/admin only)"""
    assignment = next((a for a in assignments if a.id == assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignments.remove(assignment)
    return {"message": "Assignment deleted"}

@app.post("/api/assignments/{assignment_id}/submit")
def submit_assignment(assignment_id: int, submission: AssignmentSubmission, current_user: dict = Depends(get_current_user)):
    """Submit an assignment"""
    assignment = next((a for a in assignments if a.id == assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check if late (more than 10% penalty)
    due_date = datetime.strptime(assignment.due_date, "%Y-%m-%d")
    submitted_at = datetime.now()
    is_late = submitted_at > due_date
    
    submission_data = {
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "content": submission.content,
        "file_url": submission.file_url,
        "submitted_at": submitted_at.strftime("%Y-%m-%d %H:%M"),
        "is_late": is_late,
        "grade": None,
        "feedback": None
    }
    
    if assignment_id not in submissions_db:
        submissions_db[assignment_id] = []
    
    # Check for existing submission
    existing = next((s for s in submissions_db[assignment_id] if s["user_id"] == current_user["id"]), None)
    if existing:
        existing.update(submission_data)
    else:
        submissions_db[assignment_id].append(submission_data)
    
    # Update assignment status
    assignment.status = "submitted"
    
    return {**submission_data, "is_late": is_late, "message": "Assignment submitted successfully" + (" (LATE - 10% penalty will apply)" if is_late else "")}

@app.get("/api/assignments/{assignment_id}/submissions")
def get_submissions(assignment_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Get all submissions for an assignment (instructor/admin only)"""
    assignment = next((a for a in assignments if a.id == assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return submissions_db.get(assignment_id, [])

@app.post("/api/assignments/{assignment_id}/grade")
def grade_submission(assignment_id: int, user_id: int, grade_data: GradeSubmission, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Grade a submission (instructor/admin only)"""
    assignment = next((a for a in assignments if a.id == assignment_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment_id not in submissions_db:
        raise HTTPException(status_code=404, detail="No submissions found")
    
    submission = next((s for s in submissions_db[assignment_id] if s["user_id"] == user_id), None)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Apply late penalty if applicable
    final_grade = grade_data.grade
    if submission["is_late"]:
        final_grade = int(grade_data.grade * 0.9)  # 10% penalty
    
    submission["grade"] = final_grade
    submission["feedback"] = grade_data.feedback
    
    # Update assignment grade if this is the first grade
    if assignment.grade is None:
        assignment.grade = final_grade
        assignment.status = "graded"
    
    return {
        "user_id": user_id,
        "grade": final_grade,
        "original_grade": grade_data.grade,
        "late_penalty_applied": submission["is_late"],
        "feedback": grade_data.feedback
    }

@app.get("/api/instructor/assignments")
def get_instructor_assignments(current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Get all assignments for instructor's courses"""
    instructor_courses = [c for c in courses if c.instructor.id == current_user["id"]]
    course_ids = [c.id for c in instructor_courses]
    return [a for a in assignments if a.course_id in course_ids]

# Quiz/Exam Endpoints
@app.post("/api/quizzes", status_code=201)
def create_quiz(quiz_data: QuizCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Create a new quiz (instructor/admin only)"""
    course = next((c for c in courses if c.id == quiz_data.course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_quiz = Quiz(
        id=len(quizzes) + 1,
        title=quiz_data.title,
        course_id=quiz_data.course_id,
        course_name=course.title,
        description=quiz_data.description,
        time_limit=quiz_data.time_limit,
        questions=[],
        total_points=0,
        passing_score=quiz_data.passing_score
    )
    quizzes.append(new_quiz)
    return new_quiz

@app.get("/api/quizzes/{quiz_id}")
def get_quiz(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get quiz details"""
    quiz = next((q for q in quizzes if q.id == quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

@app.get("/api/quizzes/{quiz_id}/questions")
def get_quiz_questions(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get quiz questions (without correct answers for students)"""
    quiz = next((q for q in quizzes if q.id == quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # For students, hide correct answers
    if current_user["role"] == Role.STUDENT:
        questions = []
        for q in quiz.questions:
            q_dict = q.dict()
            q_dict.pop("correct_answer")
            questions.append(q_dict)
        return questions
    
    return quiz.questions

@app.post("/api/quizzes/{quiz_id}/questions")
def add_question(quiz_id: int, question: QuestionCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Add a question to a quiz (instructor/admin only)"""
    quiz = next((q for q in quizzes if q.id == quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    new_question = QuizQuestion(
        id=len(quiz.questions) + 1,
        question=question.question,
        type=question.type,
        options=question.options,
        correct_answer=question.correct_answer,
        points=question.points
    )
    quiz.questions.append(new_question)
    quiz.total_points += question.points
    return new_question

@app.put("/api/quizzes/{quiz_id}/questions/{question_id}")
def update_question(quiz_id: int, question_id: int, question: QuestionCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Update a quiz question (instructor/admin only)"""
    quiz = next((q for q in quizzes if q.id == quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    existing = next((q for q in quiz.questions if q.id == question_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Update total points
    quiz.total_points -= existing.points
    quiz.total_points += question.points
    
    existing.question = question.question
    existing.type = question.type
    existing.options = question.options
    existing.correct_answer = question.correct_answer
    existing.points = question.points
    return existing

@app.delete("/api/quizzes/{quiz_id}/questions/{question_id}")
def delete_question(quiz_id: int, question_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Delete a quiz question (instructor/admin only)"""
    quiz = next((q for q in quizzes if q.id == quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    question = next((q for q in quiz.questions if q.id == question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    quiz.total_points -= question.points
    quiz.questions.remove(question)
    return {"message": "Question deleted"}

@app.post("/api/quizzes/{quiz_id}/submit")
def submit_quiz(quiz_id: int, submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
    """Submit quiz answers and get auto-graded results"""
    quiz = next((q for q in quizzes if q.id == quiz_id), None)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calculate score
    score = 0
    total_points = 0
    results = []
    
    for answer in submission.answers:
        question = next((q for q in quiz.questions if q.id == answer.question_id), None)
        if question:
            total_points += question.points
            is_correct = answer.answer.strip().lower() == question.correct_answer.strip().lower()
            if is_correct:
                score += question.points
            results.append({
                "question_id": answer.question_id,
                "question": question.question,
                "your_answer": answer.answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "points": question.points if is_correct else 0
            })
    
    percentage = int((score / total_points * 100) if total_points > 0 else 0)
    passed = percentage >= quiz.passing_score
    
    # Store attempt
    attempt = {
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "score": score,
        "total_points": total_points,
        "percentage": percentage,
        "passed": passed,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "results": results
    }
    
    if quiz_id not in quiz_attempts_db:
        quiz_attempts_db[quiz_id] = []
    quiz_attempts_db[quiz_id].append(attempt)
    
    return {
        "score": score,
        "total_points": total_points,
        "percentage": percentage,
        "passed": passed,
        "passing_score": quiz.passing_score,
        "results": results
    }

@app.get("/api/quizzes/{quiz_id}/attempts")
def get_quiz_attempts(quiz_id: int, current_user: dict = Depends(get_current_user)):
    """Get user's quiz attempts"""
    attempts = quiz_attempts_db.get(quiz_id, [])
    user_attempts = [a for a in attempts if a["user_id"] == current_user["id"]]
    return user_attempts

@app.get("/api/quizzes/{quiz_id}/all-attempts")
def get_all_attempts(quiz_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Get all attempts for a quiz (instructor/admin only)"""
    return quiz_attempts_db.get(quiz_id, [])

@app.get("/api/courses/{course_id}/quizzes")
def get_course_quizzes(course_id: int):
    """Get all quizzes for a course"""
    return [q for q in quizzes if q.course_id == course_id]

@app.get("/api/instructor/quizzes")
def get_instructor_quizzes(current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Get all quizzes for instructor's courses"""
    instructor_courses = [c for c in courses if c.instructor.id == current_user["id"]]
    course_ids = [c.id for c in instructor_courses]
    return [q for q in quizzes if q.course_id in course_ids]

# Discussion Forum Endpoints
@app.get("/api/courses/{course_id}/discussions")
def get_course_discussions(course_id: int):
    """Get all discussion posts for a course"""
    posts = [p for p in discussion_posts if p.course_id == course_id]
    # Sort: pinned first, then by upvotes
    posts.sort(key=lambda x: (not x.is_pinned, -x.upvotes))
    return posts

@app.post("/api/discussions", status_code=201)
def create_discussion(post: PostCreate, current_user: dict = Depends(get_current_user)):
    """Create a new discussion post"""
    course = next((c for c in courses if c.id == post.course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_post = DiscussionPost(
        id=len(discussion_posts) + 1,
        course_id=post.course_id,
        user_id=current_user["id"],
        user_name=current_user["name"],
        user_avatar=current_user["avatar"],
        title=post.title,
        content=post.content,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        upvotes=0,
        is_pinned=False,
        reply_count=0
    )
    discussion_posts.append(new_post)
    post_upvotes[new_post.id] = []
    post_replies[new_post.id] = []
    return new_post

@app.get("/api/discussions/{post_id}")
def get_discussion(post_id: int):
    """Get a discussion post with replies"""
    post = next((p for p in discussion_posts if p.id == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    replies = post_replies.get(post_id, [])
    return {"post": post, "replies": replies}

@app.post("/api/discussions/{post_id}/replies")
def add_reply(post_id: int, reply: ReplyCreate, current_user: dict = Depends(get_current_user)):
    """Add a reply to a discussion post"""
    post = next((p for p in discussion_posts if p.id == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post_id not in post_replies:
        post_replies[post_id] = []
    
    new_reply = Reply(
        id=len(post_replies[post_id]) + 1,
        post_id=post_id,
        user_id=current_user["id"],
        user_name=current_user["name"],
        user_avatar=current_user["avatar"],
        content=reply.content,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        upvotes=0
    )
    post_replies[post_id].append(new_reply)
    reply_upvotes[new_reply.id] = []
    
    # Update reply count
    post.reply_count += 1
    
    return new_reply

@app.post("/api/discussions/{post_id}/upvote")
def upvote_post(post_id: int, current_user: dict = Depends(get_current_user)):
    """Upvote or remove upvote from a post"""
    post = next((p for p in discussion_posts if p.id == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post_id not in post_upvotes:
        post_upvotes[post_id] = []
    
    user_id = current_user["id"]
    if user_id in post_upvotes[post_id]:
        # Remove upvote
        post_upvotes[post_id].remove(user_id)
        post.upvotes -= 1
        return {"upvoted": False, "upvotes": post.upvotes}
    else:
        # Add upvote
        post_upvotes[post_id].append(user_id)
        post.upvotes += 1
        return {"upvoted": True, "upvotes": post.upvotes}

@app.post("/api/discussions/{post_id}/replies/{reply_id}/upvote")
def upvote_reply(post_id: int, reply_id: int, current_user: dict = Depends(get_current_user)):
    """Upvote or remove upvote from a reply"""
    if post_id not in post_replies:
        raise HTTPException(status_code=404, detail="Post not found")
    
    reply = next((r for r in post_replies[post_id] if r.id == reply_id), None)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    
    if reply_id not in reply_upvotes:
        reply_upvotes[reply_id] = []
    
    user_id = current_user["id"]
    if user_id in reply_upvotes[reply_id]:
        # Remove upvote
        reply_upvotes[reply_id].remove(user_id)
        reply.upvotes -= 1
        return {"upvoted": False, "upvotes": reply.upvotes}
    else:
        # Add upvote
        reply_upvotes[reply_id].append(user_id)
        reply.upvotes += 1
        return {"upvoted": True, "upvotes": reply.upvotes}

@app.post("/api/discussions/{post_id}/pin")
def pin_post(post_id: int, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Pin or unpin a discussion post (instructor/admin only)"""
    post = next((p for p in discussion_posts if p.id == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.is_pinned = not post.is_pinned
    return {"pinned": post.is_pinned}

@app.delete("/api/discussions/{post_id}")
def delete_post(post_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a discussion post (author or instructor/admin only)"""
    post = next((p for p in discussion_posts if p.id == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is author or instructor/admin
    if post.user_id != current_user["id"] and current_user["role"] not in [Role.INSTRUCTOR, Role.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    discussion_posts.remove(post)
    if post_id in post_replies:
        del post_replies[post_id]
    if post_id in post_upvotes:
        del post_upvotes[post_id]
    
    return {"message": "Post deleted"}

# Certificate Generation Endpoints
def generate_verification_code() -> str:
    """Generate a unique 12-character verification code"""
    return secrets.token_urlsafe(9)[:12].upper()

def check_completion_criteria(user_id: int, course_id: int) -> tuple[bool, str]:
    """Check if user meets course completion criteria"""
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        return False, "Course not found"
    
    criteria = course_completion_criteria.get(course_id, CompletionCriteria())
    
    # Check progress
    user_progress = progress_db.get(user_id, {})
    completed_lessons = user_progress.get(course_id, [])
    total_lessons = sum(len(m.lessons) for m in course.modules)
    progress_percent = int((len(completed_lessons) / total_lessons * 100) if total_lessons > 0 else 0)
    
    if progress_percent < criteria.min_progress:
        return False, f"Need {criteria.min_progress}% progress (current: {progress_percent}%)"
    
    # Check assignments if required
    if criteria.required_assignments:
        course_assignments = [a for a in assignments if a.course_id == course_id]
        if course_assignments:
            user_submissions = []
            for assignment in course_assignments:
                subs = submissions_db.get(assignment.id, [])
                user_sub = next((s for s in subs if s["user_id"] == user_id and s.get("grade") is not None), None)
                if user_sub:
                    user_submissions.append(user_sub)
            
            if len(user_submissions) < len(course_assignments):
                return False, "All assignments must be completed and graded"
    
    # Check quizzes if required
    if criteria.required_quizzes:
        course_quizzes = [q for q in quizzes if q.course_id == course_id]
        if course_quizzes:
            passed_quizzes = 0
            for quiz in course_quizzes:
                attempts = quiz_attempts_db.get(quiz.id, [])
                user_attempts = [a for a in attempts if a["user_id"] == user_id]
                if user_attempts:
                    best_attempt = max(user_attempts, key=lambda x: x["percentage"])
                    if best_attempt["percentage"] >= criteria.min_quiz_score:
                        passed_quizzes += 1
            
            if passed_quizzes < len(course_quizzes):
                return False, f"Must pass all quizzes with {criteria.min_quiz_score}% or higher"
    
    return True, "All criteria met"

@app.post("/api/courses/{course_id}/certificate", status_code=201)
def generate_certificate(course_id: int, current_user: dict = Depends(get_current_user)):
    """Generate a certificate for course completion"""
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already has certificate
    existing = next((cert for cert in certificates if cert.user_id == current_user["id"] and cert.course_id == course_id), None)
    if existing:
        return existing
    
    # Check completion criteria
    meets_criteria, message = check_completion_criteria(current_user["id"], course_id)
    if not meets_criteria:
        raise HTTPException(status_code=400, detail=f"Course not completed: {message}")
    
    # Generate certificate
    new_cert = Certificate(
        id=len(certificates) + 1,
        user_id=current_user["id"],
        user_name=current_user["name"],
        course_id=course_id,
        course_name=course.title,
        instructor_name=course.instructor.name,
        issued_at=datetime.now().strftime("%Y-%m-%d"),
        verification_code=generate_verification_code(),
        completion_date=datetime.now().strftime("%Y-%m-%d")
    )
    certificates.append(new_cert)
    return new_cert

@app.get("/api/users/{user_id}/certificates")
def get_user_certificates(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get all certificates for a user"""
    if current_user["id"] != user_id and current_user["role"] != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return [cert for cert in certificates if cert.user_id == user_id]

@app.get("/api/certificates/verify/{verification_code}")
def verify_certificate(verification_code: str):
    """Verify a certificate by its verification code"""
    cert = next((c for c in certificates if c.verification_code == verification_code), None)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert

@app.get("/api/courses/{course_id}/completion-status")
def get_completion_status(course_id: int, current_user: dict = Depends(get_current_user)):
    """Check if user can generate certificate"""
    meets_criteria, message = check_completion_criteria(current_user["id"], course_id)
    
    # Check if already has certificate
    has_certificate = any(cert.user_id == current_user["id"] and cert.course_id == course_id for cert in certificates)
    
    return {
        "can_generate": meets_criteria and not has_certificate,
        "has_certificate": has_certificate,
        "message": message,
        "criteria": course_completion_criteria.get(course_id, CompletionCriteria()).dict()
    }

@app.put("/api/courses/{course_id}/completion-criteria")
def set_completion_criteria(course_id: int, criteria: CompletionCriteria, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Set completion criteria for a course (instructor/admin only)"""
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course_completion_criteria[course_id] = criteria
    return criteria

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)