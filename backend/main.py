from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from enum import Enum
import re
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


class CourseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Course(BaseModel):
    id: int
    title: str
    description: str
    instructor: Instructor
    category: str
    level: CourseLevel = CourseLevel.BEGINNER
    thumbnail: str
    duration: str
    modules: List[Module]
    status: CourseStatus = CourseStatus.DRAFT


class CourseReview(BaseModel):
    id: int
    course_id: int
    user_id: int
    user_name: str
    user_avatar: str
    rating: int = Field(ge=1, le=5)
    content: str
    status: ReviewStatus = ReviewStatus.PENDING
    moderator_id: Optional[int] = None
    moderator_name: Optional[str] = None
    moderation_note: Optional[str] = None
    created_at: str
    moderated_at: Optional[str] = None


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str = Field(min_length=10, max_length=2000)


class ReviewModeration(BaseModel):
    status: ReviewStatus
    moderation_note: Optional[str] = None

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


class AlertPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertDueItem(BaseModel):
    assignment_id: int
    title: str
    due_date: str
    status: str


class LearningAlertItem(BaseModel):
    course_id: int
    course_title: str
    course_category: str
    instructor_name: str
    student_id: int
    student_name: str
    progress_percent: int
    submitted_assignments: int
    graded_assignments: int
    overdue_assignments: int
    due_soon_assignments: int
    average_grade: Optional[float] = None
    best_quiz_score: Optional[float] = None
    risk_score: float
    priority: AlertPriority
    reasons: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    due_items: List[AlertDueItem] = Field(default_factory=list)


class AlertSummary(BaseModel):
    tracked_items: int
    needs_attention: int
    high_priority: int
    average_progress: float
    overdue_assignments: int


class RiskStatus(str, Enum):
    SAFE = "safe"
    AT_RISK = "at risk"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"


class MonitoringStatus(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    HIGH_CONCERN = "high concern"


class AttendanceEvent(BaseModel):
    learner_id: int
    course_id: int
    session_date: str
    status: Optional[AttendanceStatus] = None
    source: Optional[str] = None
    is_cancelled: bool = False
    timestamp: Optional[str] = None


class AssignmentCompletionEvent(BaseModel):
    learner_id: int
    course_id: int
    assignment_id: int
    assignment_title: Optional[str] = None
    submitted_at: Optional[str] = None
    deadline: Optional[str] = None
    content: Optional[str] = None
    file_url: Optional[str] = None
    score: Optional[float] = None
    is_optional: bool = False


class QuizPerformanceEvent(BaseModel):
    learner_id: int
    course_id: int
    quiz_category: str
    score: Optional[float] = None
    course_average: Optional[float] = None
    quiz_id: Optional[int] = None
    timestamp: Optional[str] = None


class ActivityEvent(BaseModel):
    learner_id: int
    course_id: int
    activity_at: Optional[str] = None
    active: Optional[bool] = None
    timestamp: Optional[str] = None


class LearnerCourseState(BaseModel):
    learner_id: int
    course_id: int
    learner_name: str = ""
    course_name: str = ""
    course_code: str = ""
    attendance_total: int = 0
    attendance_present: int = 0
    attendance_late: int = 0
    attendance_absent: int = 0
    attendance_percentage: float = 0.0
    attendance_flagged: bool = False
    attendance_follow_up: bool = False
    attendance_last_reset: str = ""
    monthly_absences: int = 0
    assignment_total: int = 0
    assignment_complete: int = 0
    assignment_percentage: float = 0.0
    assignment_last_score: float = 0.0
    assignment_latest_submission: str = ""
    quiz_total: int = 0
    quiz_score_average: float = 0.0
    quiz_last_category: str = ""
    recent_activity_active: bool = False
    recent_activity_at: str = ""
    risk_score: float = 0.0
    risk_label: str = "safe"
    risk_status: str = "safe"
    last_updated_at: str = ""
    risk_last_alert_at: str = ""
    risk_alert_open: bool = False


class LearnerMonitoringCard(BaseModel):
    learner_id: int
    learner_name: str
    course_id: int
    course_name: str
    course_code: str
    attendance_percentage: float
    completion_percentage: float
    risk_score: float
    risk_label: str
    status: str
    overall_status: str


class NotificationItem(BaseModel):
    id: int
    learner_id: int
    course_id: int
    learner_name: str
    course_name: str
    status: str
    score: float
    payload: dict
    channel_status: str
    created_at: str
    updated_at: str
    delivered_at: Optional[str] = None


class NotificationSummary(BaseModel):
    total: int
    queued: int
    delivered: int
    latest_status: str


class MonitoringSummary(BaseModel):
    learners: int
    at_risk: int
    follow_up: int
    below_attendance_target: int
    below_completion_target: int


class MonitoringResponse(BaseModel):
    generated_at: str
    summary: MonitoringSummary
    learners: List[LearnerMonitoringCard]
    notifications: NotificationSummary


class MonitorExportRow(BaseModel):
    learner_id: int
    learner_name: str
    course_id: int
    course_name: str
    course_code: str
    attendance_percentage: str
    completion_percentage: str
    risk_score: str
    risk_label: str
    status: str


class MonitoringChartBucket(BaseModel):
    label: str
    count: int


class MonitoringAnalyticsResponse(BaseModel):
    generated_at: str
    summary_text: str
    buckets: List[MonitoringChartBucket]
    categories: List[MonitoringChartBucket]


class MonitoringEventEnvelope(BaseModel):
    timestamp: Optional[str] = None
    learner_id: int
    course_id: int
    learner_name: Optional[str] = None
    course_name: Optional[str] = None
    course_code: Optional[str] = None


class LearningAlertResponse(BaseModel):
    scope: str
    generated_at: str
    summary: AlertSummary
    alerts: List[LearningAlertItem]


class AnalyticsCourseMetric(BaseModel):
    course_id: int
    course_title: str
    views: int
    enrollments: int
    completions: int
    completion_rate: float
    avg_progress: float
    revenue: float


class InstructorAnalyticsResponse(BaseModel):
    summary: dict
    engagement: dict
    earnings: dict
    courses: List[AnalyticsCourseMetric]

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
    level: CourseLevel = CourseLevel.BEGINNER
    thumbnail: str
    duration: str
    modules: List[ModuleCreate] = []

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[CourseLevel] = None
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
        level=CourseLevel.BEGINNER,
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
        level=CourseLevel.INTERMEDIATE,
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
        level=CourseLevel.BEGINNER,
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
        level=CourseLevel.INTERMEDIATE,
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
        level=CourseLevel.ADVANCED,
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
        level=CourseLevel.ADVANCED,
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

# Course analytics stores
course_views: dict[int, int] = {
    1: 120,
    2: 90,
    3: 75,
    4: 60,
    5: 110,
    6: 85,
}
course_prices: dict[int, float] = {
    1: 89.0,
    2: 99.0,
    3: 79.0,
    4: 69.0,
    5: 119.0,
    6: 129.0,
}

# Course discovery and review data
course_search_popularity: dict[str, int] = {
    "python": 22,
    "design": 16,
    "data science": 14,
    "machine learning": 12,
    "figma": 8,
}

course_reviews: List[CourseReview] = [
    CourseReview(
        id=1,
        course_id=1,
        user_id=1,
        user_name="Alex Rivera",
        user_avatar="AR",
        rating=5,
        content="Very practical and beginner friendly. The exercises made every concept click quickly.",
        status=ReviewStatus.APPROVED,
        moderator_id=3,
        moderator_name="Casey Morgan",
        created_at="2024-02-14 10:10:00",
        moderated_at="2024-02-14 11:00:00",
    ),
    CourseReview(
        id=2,
        course_id=3,
        user_id=1,
        user_name="Alex Rivera",
        user_avatar="AR",
        rating=4,
        content="Great examples on typography and hierarchy. Would love more section-by-section critiques.",
        status=ReviewStatus.APPROVED,
        moderator_id=2,
        moderator_name="Jordan Lee",
        created_at="2024-02-20 09:30:00",
        moderated_at="2024-02-20 10:05:00",
    ),
    CourseReview(
        id=3,
        course_id=5,
        user_id=1,
        user_name="Alex Rivera",
        user_avatar="AR",
        rating=5,
        content="Dense content but very useful. The Pandas and visualization units are excellent.",
        status=ReviewStatus.PENDING,
        created_at="2024-03-02 16:45:00",
    ),
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

# Wishlist/Favorites data
wishlist_items: dict[int, List[int]] = {}  # {user_id: [course_ids]}

# Notifications data
class NotificationType(str, Enum):
    ASSIGNMENT = "assignment"
    ANNOUNCEMENT = "announcement"
    GRADE = "grade"
    DISCUSSION = "discussion"
    COURSE_UPDATE = "course_update"
    CERTIFICATE = "certificate"

class Notification(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    title: str
    message: str
    link: Optional[str] = None
    read: bool = False
    created_at: str

class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str
    message: str
    link: Optional[str] = None

class NotificationPreferences(BaseModel):
    email_assignments: bool = True
    email_announcements: bool = True
    email_grades: bool = True
    email_discussions: bool = False
    push_assignments: bool = True
    push_announcements: bool = True
    push_grades: bool = True
    push_discussions: bool = False

notifications: List[Notification] = []
notification_preferences: dict[int, NotificationPreferences] = {}  # {user_id: preferences}

# Parent Portal data
class ParentChildRelation(BaseModel):
    parent_id: int
    child_id: int
    relation: str = "parent"  # parent, guardian
    verified: bool = False
    verification_code: str
    created_at: str

class ParentVerificationRequest(BaseModel):
    child_email: str
    relation: str = "parent"

class ParentDashboard(BaseModel):
    child_id: int
    child_name: str
    child_avatar: str
    enrolled_courses: int
    completed_courses: int
    average_progress: float
    upcoming_assignments: int
    overdue_assignments: int
    recent_grades: List[dict] = []
    recent_activity: List[dict] = []

class ParentNotificationSettings(BaseModel):
    progress_updates: bool = True
    assignment_reminders: bool = True
    grade_notifications: bool = True
    attendance_alerts: bool = True
    weekly_summary: bool = True

parent_child_relations: List[ParentChildRelation] = []
parent_notification_settings: dict[int, ParentNotificationSettings] = {}  # {parent_id: settings}
pending_verifications: dict[str, dict] = {}  # {verification_code: {parent_id, child_id}}

learner_course_state: dict[tuple[int, int], dict] = {}
monitoring_notifications: List[dict] = []
attendance_source_index: dict[tuple[int, int, str], dict] = {}
assignment_source_index: dict[tuple[int, int], dict] = {}
quiz_source_index: dict[tuple[int, int, str], dict] = {}
activity_source_index: dict[tuple[int, int], dict] = {}
alert_state_by_term: dict[tuple[int, int], dict] = {}


def _normalize_search_term(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.lower().strip().split())


def _record_search_term(value: Optional[str]) -> None:
    normalized = _normalize_search_term(value)
    if len(normalized) < 2:
        return
    course_search_popularity[normalized] = course_search_popularity.get(normalized, 0) + 1


def _duration_to_hours(value: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if not match:
        return 0.0
    return float(match.group(1))


def _duration_matches(value: str, bucket: Optional[str]) -> bool:
    if not bucket:
        return True
    hours = _duration_to_hours(value)
    normalized_bucket = bucket.lower()
    if normalized_bucket == "short":
        return hours < 10
    if normalized_bucket == "medium":
        return 10 <= hours <= 15
    if normalized_bucket == "long":
        return hours > 15
    return True


def _course_search_text(course: Course) -> str:
    module_titles = " ".join(module.title for module in course.modules)
    lesson_titles = " ".join(lesson.title for module in course.modules for lesson in module.lessons)
    values = [
        course.title,
        course.description,
        course.category,
        course.level.value,
        course.instructor.name,
        module_titles,
        lesson_titles,
    ]
    return " ".join(values).lower()


def _course_reviews_for(course_id: int, status: Optional[ReviewStatus] = None) -> List[CourseReview]:
    reviews = [review for review in course_reviews if review.course_id == course_id]
    if status is not None:
        reviews = [review for review in reviews if review.status == status]
    return reviews


def _rating_distribution(reviews: List[CourseReview]) -> Dict[str, int]:
    distribution = {str(value): 0 for value in range(1, 6)}
    for review in reviews:
        distribution[str(review.rating)] += 1
    return distribution


def _course_rating_summary(course_id: int) -> dict:
    approved_reviews = _course_reviews_for(course_id, ReviewStatus.APPROVED)
    rating_count = len(approved_reviews)
    average_rating = round(sum(review.rating for review in approved_reviews) / rating_count, 1) if rating_count else 0.0
    return {
        "average_rating": average_rating,
        "rating_count": rating_count,
    }


def _serialize_course(course: Course) -> dict:
    payload = course.model_dump(mode="json")
    payload.update(_course_rating_summary(course.id))
    return payload


def _serialize_review(review: CourseReview) -> dict:
    return review.model_dump(mode="json")


def _parse_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _safe_str(value: Optional[str]) -> str:
    return value or ""


def _safe_float(value: Optional[float]) -> float:
    if value is None:
        return 0.0
    return float(value)


def _safe_bool(value: Optional[bool]) -> bool:
    return bool(value) if value is not None else False


def _current_term_key() -> str:
    return datetime.utcnow().strftime("%Y-T%U")


def _get_course_code(course: Course) -> str:
    return f"CRS-{course.id:03d}"


def _get_or_create_state(learner_id: int, course_id: int) -> dict:
    key = (learner_id, course_id)
    if key not in learner_course_state:
        course = next((c for c in courses if c.id == course_id), None)
        learner = next((u for u in users if u.id == learner_id), None)
        learner_course_state[key] = LearnerCourseState(
            learner_id=learner_id,
            course_id=course_id,
            learner_name=learner.name if learner else "",
            course_name=course.title if course else "",
            course_code=_get_course_code(course) if course else f"CRS-{course_id:03d}",
        ).dict()
    return learner_course_state[key]


def _compare_state(candidate: dict, existing: dict) -> bool:
    candidate_ts = _parse_timestamp(candidate.get("last_updated_at"))
    existing_ts = _parse_timestamp(existing.get("last_updated_at"))
    if candidate_ts > existing_ts:
        return True
    if candidate_ts < existing_ts:
        return False
    return _safe_float(candidate.get("risk_score")) < _safe_float(existing.get("risk_score"))


def _status_from_score(score: float) -> str:
    return MonitoringStatus.HIGH_CONCERN.value if score < 0.5 else MonitoringStatus.WARNING.value if score < 0.75 else MonitoringStatus.SAFE.value


def _risk_label(score: float) -> str:
    return RiskStatus.AT_RISK.value if score < 0.5 else RiskStatus.SAFE.value


def _attendance_ratio(state: dict) -> float:
    total = state.get("attendance_total", 0) or 0
    if total <= 0:
        return 0.0
    present = state.get("attendance_present", 0) or 0
    late = state.get("attendance_late", 0) or 0
    return round(((present + (late * 0.5)) / total) * 100, 2)


def _completion_ratio(state: dict) -> float:
    total = state.get("assignment_total", 0) or 0
    if total <= 0:
        return 0.0
    complete = state.get("assignment_complete", 0) or 0
    return round((complete / total) * 100, 2)


def _calculate_risk_score(state: dict) -> float:
    attendance_component = 1.0 - (_attendance_ratio(state) / 100.0)
    completion_component = 1.0 - (_completion_ratio(state) / 100.0)
    quiz_component = 1.0 - (_safe_float(state.get("quiz_score_average")) / 100.0)
    if state.get("quiz_total", 0) <= 0:
        quiz_component = 1.0 - (state.get("quiz_score_average", 0.0) / 100.0)
    activity_component = 0.0 if state.get("recent_activity_active", False) else 1.0
    risk_score = (attendance_component * 0.3) + (completion_component * 0.35) + (quiz_component * 0.25) + (activity_component * 0.1)
    return round(max(0.0, min(1.0, risk_score)), 2)


def _refresh_state_labels(state: dict) -> dict:
    score = _calculate_risk_score(state)
    existing_score = _safe_float(state.get("risk_score"))
    if state.get("risk_label"):
        if score <= existing_score:
            state["risk_score"] = score
            state["risk_label"] = _risk_label(score)
            state["risk_status"] = _status_from_score(score)
    else:
        state["risk_score"] = score
        state["risk_label"] = _risk_label(score)
        state["risk_status"] = _status_from_score(score)
    if not state.get("risk_label"):
        state["risk_score"] = score
        state["risk_label"] = _risk_label(score)
        state["risk_status"] = _status_from_score(score)
    state["last_updated_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return state


def _ensure_notification(learner_id: int, course_id: int, status: str, score: float, triggered_at: Optional[str] = None) -> dict:
    course = next((c for c in courses if c.id == course_id), None)
    learner = next((u for u in users if u.id == learner_id), None)
    state = _get_or_create_state(learner_id, course_id)
    created_at = triggered_at or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "learner_name": state.get("learner_name") or (learner.name if learner else str(learner_id)),
        "course_name": state.get("course_name") or (course.title if course else str(course_id)),
        "status": status,
        "score": round(score, 2),
    }
    notification = next((item for item in monitoring_notifications if item["learner_id"] == learner_id and item["course_id"] == course_id and item["status"] == status and item["created_at"][:10] == created_at[:10]), None)
    if notification:
        notification["payload"] = {**notification["payload"], **payload}
        notification["updated_at"] = created_at
        notification["channel_status"] = "queued"
        return notification
    new_item = {
        "id": len(monitoring_notifications) + 1,
        "learner_id": learner_id,
        "course_id": course_id,
        "learner_name": payload["learner_name"],
        "course_name": payload["course_name"],
        "status": status,
        "score": round(score, 2),
        "payload": payload,
        "channel_status": "queued",
        "created_at": created_at,
        "updated_at": created_at,
        "delivered_at": None,
    }
    monitoring_notifications.append(new_item)
    return new_item


def _update_risk_notification(state: dict) -> None:
    key = (state["learner_id"], state["course_id"])
    term_key = _current_term_key()
    alert_state = alert_state_by_term.setdefault(key, {"term": term_key, "was_at_risk": False, "last_score": 1.0})
    score = _safe_float(state.get("risk_score"))
    at_risk = score < 0.5

    if alert_state["term"] != term_key:
        alert_state["term"] = term_key
        alert_state["was_at_risk"] = False

    if at_risk and (not alert_state["was_at_risk"] or _safe_float(alert_state.get("last_score", 1.0)) >= 0.5):
        _ensure_notification(state["learner_id"], state["course_id"], "at risk", score)
        state["risk_alert_open"] = True
        state["risk_last_alert_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        alert_state["was_at_risk"] = True
    elif not at_risk:
        state["risk_alert_open"] = False
        alert_state["was_at_risk"] = False

    alert_state["last_score"] = score


def _persist_state(candidate: dict) -> dict:
    key = (candidate["learner_id"], candidate["course_id"])
    existing = learner_course_state.get(key)
    if existing and not _compare_state(candidate, existing):
        return existing
    learner_course_state[key] = candidate
    _update_risk_notification(candidate)
    return candidate


def _build_monitoring_card(state: dict) -> LearnerMonitoringCard:
    attendance = _safe_float(state.get("attendance_percentage"))
    completion = _safe_float(state.get("assignment_percentage"))
    risk = _safe_float(state.get("risk_score"))
    values = [attendance / 100.0, completion / 100.0, risk]
    overall = min(values) if values else 0.0
    return LearnerMonitoringCard(
        learner_id=state.get("learner_id", 0),
        learner_name=_safe_str(state.get("learner_name")) or str(state.get("learner_id", 0)),
        course_id=state.get("course_id", 0),
        course_name=_safe_str(state.get("course_name")) or _safe_str(state.get("course_code")),
        course_code=_safe_str(state.get("course_code")),
        attendance_percentage=round(attendance, 2),
        completion_percentage=round(completion, 2),
        risk_score=round(risk, 2),
        risk_label=_safe_str(state.get("risk_label")) or _risk_label(risk),
        status=_status_from_score(risk),
        overall_status=_status_from_score(overall),
    )


def _query_states(course_id: Optional[int] = None) -> List[dict]:
    states = list(learner_course_state.values())
    if course_id is not None:
        states = [state for state in states if state.get("course_id") == course_id]
    return states


def _update_attendance_state(event: AttendanceEvent, timestamp: datetime) -> dict:
    key = (event.learner_id, event.course_id, event.session_date)
    existing = attendance_source_index.get(key)
    if existing and existing.get("source") == "imported" and event.source != "imported":
        return _get_or_create_state(event.learner_id, event.course_id)

    effective_status = event.status or AttendanceStatus.ABSENT
    state = _get_or_create_state(event.learner_id, event.course_id)
    state["attendance_total"] = state.get("attendance_total", 0) + 1
    if effective_status == AttendanceStatus.PRESENT:
        state["attendance_present"] = state.get("attendance_present", 0) + 1
    elif effective_status == AttendanceStatus.LATE:
        state["attendance_late"] = state.get("attendance_late", 0) + 1
    else:
        state["attendance_absent"] = state.get("attendance_absent", 0) + 1
        state["monthly_absences"] = state.get("monthly_absences", 0) + 1

    state["attendance_percentage"] = _attendance_ratio(state)
    state["attendance_flagged"] = state["attendance_percentage"] < 80.0
    state["attendance_follow_up"] = state.get("attendance_follow_up", False) or state.get("monthly_absences", 0) > 3
    state["last_updated_at"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    attendance_source_index[key] = {
        "source": event.source or "manual",
        "status": effective_status.value,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return _refresh_state_labels(state)


def _update_assignment_state(event: AssignmentCompletionEvent, timestamp: datetime) -> dict:
    key = (event.learner_id, event.assignment_id)
    existing = assignment_source_index.get(key)
    candidate_timestamp = _parse_timestamp(event.submitted_at) if event.submitted_at else timestamp
    if existing and _parse_timestamp(existing.get("submitted_at")) > candidate_timestamp:
        return _get_or_create_state(event.learner_id, event.course_id)

    state = _get_or_create_state(event.learner_id, event.course_id)
    content = _safe_str(event.content)
    has_file = bool(event.file_url)
    is_complete = bool(content.strip()) or has_file
    state["assignment_total"] = state.get("assignment_total", 0) + 1
    if is_complete:
        state["assignment_complete"] = state.get("assignment_complete", 0) + 1
    state["assignment_percentage"] = _completion_ratio(state)
    state["assignment_last_score"] = _safe_float(event.score)
    state["assignment_latest_submission"] = candidate_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    assignment_source_index[key] = {
        "submitted_at": candidate_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "score": _safe_float(event.score),
        "is_optional": _safe_bool(event.is_optional),
    }
    return _refresh_state_labels(state)


def _update_quiz_state(event: QuizPerformanceEvent, timestamp: datetime) -> dict:
    state = _get_or_create_state(event.learner_id, event.course_id)
    key = (event.learner_id, event.course_id, event.quiz_category)
    quiz_score = _safe_float(event.score)
    if quiz_score <= 0 and event.course_average is not None:
        quiz_score = _safe_float(event.course_average)
    previous = quiz_source_index.get(key)
    if previous and _parse_timestamp(previous.get("timestamp")) > timestamp:
        return state
    state["quiz_total"] = state.get("quiz_total", 0) + 1
    total_score = state.get("quiz_score_average", 0.0) * (state["quiz_total"] - 1)
    state["quiz_score_average"] = round((total_score + quiz_score) / state["quiz_total"], 2)
    state["quiz_last_category"] = event.quiz_category
    quiz_source_index[key] = {
        "score": quiz_score,
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return _refresh_state_labels(state)


def _update_activity_state(event: ActivityEvent, timestamp: datetime) -> dict:
    state = _get_or_create_state(event.learner_id, event.course_id)
    key = (event.learner_id, event.course_id)
    previous = activity_source_index.get(key)
    if previous and _parse_timestamp(previous.get("timestamp")) > timestamp:
        return state
    active = _safe_bool(event.active)
    state["recent_activity_active"] = active if event.activity_at or event.active is not None else False
    state["recent_activity_at"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    activity_source_index[key] = {"active": state["recent_activity_active"], "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")}
    return _refresh_state_labels(state)


def _persist_monitoring_payload(state: dict, event: dict) -> dict:
    state["learner_name"] = _safe_str(event.get("learner_name")) or state.get("learner_name", "")
    state["course_name"] = _safe_str(event.get("course_name")) or state.get("course_name", "")
    state["course_code"] = _safe_str(event.get("course_code")) or state.get("course_code", "")
    state["last_updated_at"] = _safe_str(event.get("timestamp")) or state.get("last_updated_at", "") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return _persist_state(state)


@app.post("/api/monitoring/events")
def record_monitoring_event(event: MonitoringEventEnvelope, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN, Role.STUDENT))):
    state = _get_or_create_state(event.learner_id, event.course_id)
    return _persist_monitoring_payload(state, event.dict())


@app.get("/api/monitoring/learners", response_model=MonitoringResponse)
def get_monitoring_learners(course_id: Optional[int] = None, search: Optional[str] = None, status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    states = _query_states(course_id)
    cards = [_build_monitoring_card(state) for state in states]
    if search:
        search_value = search.lower()
        cards = [card for card in cards if search_value in card.learner_name.lower() or search_value in card.course_name.lower() or search_value in card.status.lower()]
    if status:
        cards = [card for card in cards if card.status == status]
    cards.sort(key=lambda item: (item.overall_status != MonitoringStatus.HIGH_CONCERN.value, item.overall_status != MonitoringStatus.WARNING.value, item.risk_score, item.attendance_percentage))
    summary = MonitoringSummary(
        learners=len(cards),
        at_risk=len([card for card in cards if card.status == MonitoringStatus.HIGH_CONCERN.value]),
        follow_up=len([state for state in states if state.get("attendance_follow_up")]),
        below_attendance_target=len([card for card in cards if card.attendance_percentage < 80.0]),
        below_completion_target=len([card for card in cards if card.completion_percentage < 75.0]),
    )
    notifications = NotificationSummary(
        total=len(monitoring_notifications),
        queued=len([item for item in monitoring_notifications if item["channel_status"] == "queued"]),
        delivered=len([item for item in monitoring_notifications if item["channel_status"] == "delivered"]),
        latest_status=monitoring_notifications[0]["status"] if monitoring_notifications else "",
    )
    return MonitoringResponse(generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), summary=summary, learners=cards, notifications=notifications)


@app.get("/api/monitoring/learners/{learner_id}/{course_id}")
def get_monitoring_state(learner_id: int, course_id: int, current_user: dict = Depends(get_current_user)):
    state = _get_or_create_state(learner_id, course_id)
    card = _build_monitoring_card(state)
    return {**state, **card.dict()}


@app.post("/api/monitoring/attendance")
def record_attendance(event: AttendanceEvent, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    state = _update_attendance_state(event, datetime.utcnow())
    return _build_monitoring_card(state)


@app.post("/api/monitoring/assignments")
def record_assignment_completion(event: AssignmentCompletionEvent, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    state = _update_assignment_state(event, _parse_timestamp(event.submitted_at))
    return _build_monitoring_card(state)


@app.post("/api/monitoring/quizzes")
def record_quiz_performance(event: QuizPerformanceEvent, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    state = _update_quiz_state(event, _parse_timestamp(event.timestamp))
    return _build_monitoring_card(state)


@app.post("/api/monitoring/activity")
def record_activity(event: ActivityEvent, current_user: dict = Depends(get_current_user)):
    state = _update_activity_state(event, _parse_timestamp(event.timestamp))
    return _build_monitoring_card(state)


@app.get("/api/monitoring/export")
def export_monitoring(course_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    states = [_build_monitoring_card(state) for state in _query_states(course_id)]
    rows = [
        MonitorExportRow(
            learner_id=card.learner_id,
            learner_name=card.learner_name or "",
            course_id=card.course_id,
            course_name=card.course_name or "",
            course_code=next((state.get("course_code", "") for state in _query_states(course_id) if state.get("learner_id") == card.learner_id and state.get("course_id") == card.course_id), ""),
            attendance_percentage=f"{card.attendance_percentage:.2f}",
            completion_percentage=f"{card.completion_percentage:.2f}",
            risk_score=f"{card.risk_score:.2f}",
            risk_label=card.risk_label,
            status=card.status,
        ).dict()
        for card in states
    ]
    return {"rows": rows}


@app.get("/api/monitoring/analytics", response_model=MonitoringAnalyticsResponse)
def get_monitoring_analytics(course_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    states = _query_states(course_id)
    counts = {MonitoringStatus.SAFE.value: 0, MonitoringStatus.WARNING.value: 0, MonitoringStatus.HIGH_CONCERN.value: 0}
    for state in states:
        counts[_status_from_score(_safe_float(state.get("risk_score")))] += 1
    categories = [
        MonitoringChartBucket(label="High concern", count=counts[MonitoringStatus.HIGH_CONCERN.value]),
        MonitoringChartBucket(label="Warning", count=counts[MonitoringStatus.WARNING.value]),
        MonitoringChartBucket(label="Safe", count=counts[MonitoringStatus.SAFE.value]),
    ]
    summary_text = f"{counts[MonitoringStatus.HIGH_CONCERN.value]} learners are in high concern, {counts[MonitoringStatus.WARNING.value]} are in warning, and {counts[MonitoringStatus.SAFE.value]} are safe."
    return MonitoringAnalyticsResponse(
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        summary_text=summary_text,
        buckets=[
            MonitoringChartBucket(label="Safe", count=counts[MonitoringStatus.SAFE.value]),
            MonitoringChartBucket(label="Warning", count=counts[MonitoringStatus.WARNING.value]),
            MonitoringChartBucket(label="High concern", count=counts[MonitoringStatus.HIGH_CONCERN.value]),
        ],
        categories=categories,
    )


@app.get("/api/notifications")
def get_notifications(current_user: dict = Depends(get_current_user)):
    items = sorted(monitoring_notifications, key=lambda item: item["created_at"], reverse=True)
    return {"items": items, "summary": NotificationSummary(total=len(items), queued=len([item for item in items if item["channel_status"] == "queued"]), delivered=len([item for item in items if item["channel_status"] == "delivered"]), latest_status=items[0]["status"] if items else "").dict()}


@app.post("/api/notifications/retry")
def retry_notifications(current_user: dict = Depends(require_role(Role.ADMIN, Role.INSTRUCTOR))):
    queued = [item for item in sorted(monitoring_notifications, key=lambda item: item["created_at"]) if item["channel_status"] == "queued"]
    for item in queued:
        item["channel_status"] = "delivered"
        item["delivered_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return {"retried": len(queued)}


@app.post("/api/monitoring/reset-follow-up")
def reset_follow_up(current_user: dict = Depends(require_role(Role.ADMIN))):
    for state in learner_course_state.values():
        if state.get("monthly_absences", 0) == 0:
            state["attendance_follow_up"] = False
    return {"message": "Follow-up flags reset"}

# Endpoints
@app.get("/api/courses")
def get_courses(
    category: Optional[str] = None,
    search: Optional[str] = None,
    duration: Optional[str] = None,
    level: Optional[CourseLevel] = None,
    min_rating: Optional[float] = None,
):
    result = courses
    if category:
        result = [course for course in result if course.category.lower() == category.lower()]
    if level:
        result = [course for course in result if course.level == level]
    if duration:
        result = [course for course in result if _duration_matches(course.duration, duration)]
    if search:
        normalized_search = _normalize_search_term(search)
        search_terms = [term for term in normalized_search.split(" ") if term]
        if search_terms:
            result = [
                course
                for course in result
                if all(term in _course_search_text(course) for term in search_terms)
            ]
            _record_search_term(search)
    if min_rating is not None:
        result = [
            course for course in result
            if _course_rating_summary(course.id)["average_rating"] >= min_rating
        ]
    return [_serialize_course(course) for course in result]


@app.get("/api/courses/search/suggestions")
def get_course_search_suggestions(query: str = "", limit: int = 6):
    normalized_query = _normalize_search_term(query)
    if not normalized_query:
        return {"items": []}

    capped_limit = max(1, min(limit, 10))
    suggestions: Dict[str, dict] = {}

    def _add_suggestion(term: str) -> None:
        normalized_term = _normalize_search_term(term)
        if len(normalized_term) < 2 or normalized_query not in normalized_term:
            return
        current = suggestions.get(normalized_term)
        candidate = {
            "term": term.strip(),
            "popularity": course_search_popularity.get(normalized_term, 0),
            "starts_with": normalized_term.startswith(normalized_query),
        }
        if not current:
            suggestions[normalized_term] = candidate
            return
        if candidate["starts_with"] and not current["starts_with"]:
            suggestions[normalized_term] = candidate
            return
        if candidate["term"] and len(candidate["term"]) < len(current["term"]):
            suggestions[normalized_term] = candidate

    for term in course_search_popularity.keys():
        _add_suggestion(term)

    for course in courses:
        _add_suggestion(course.title)
        _add_suggestion(course.category)
        _add_suggestion(course.instructor.name)
        for module in course.modules:
            _add_suggestion(module.title)
            for lesson in module.lessons:
                _add_suggestion(lesson.title)

    ordered = sorted(
        suggestions.values(),
        key=lambda item: (not item["starts_with"], -item["popularity"], len(item["term"])),
    )
    return {"items": [item["term"] for item in ordered[:capped_limit]]}


@app.get("/api/courses/search/popular")
def get_popular_course_searches(limit: int = 6):
    capped_limit = max(1, min(limit, 20))
    popular = sorted(course_search_popularity.items(), key=lambda item: (-item[1], item[0]))
    return {
        "items": [
            {"term": term, "count": count}
            for term, count in popular[:capped_limit]
        ]
    }

@app.get("/api/courses/{course_id}")
def get_course(course_id: int):
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course_views[course_id] = course_views.get(course_id, 0) + 1
    return _serialize_course(course)


@app.get("/api/courses/{course_id}/reviews")
def get_course_reviews(course_id: int):
    course = next((item for item in courses if item.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    approved_reviews = sorted(
        _course_reviews_for(course_id, ReviewStatus.APPROVED),
        key=lambda review: review.created_at,
        reverse=True,
    )
    return {
        "summary": _course_rating_summary(course_id),
        "distribution": _rating_distribution(approved_reviews),
        "reviews": [_serialize_review(review) for review in approved_reviews],
    }


@app.post("/api/courses/{course_id}/reviews")
def create_course_review(
    course_id: int,
    review_data: ReviewCreate,
    current_user: dict = Depends(get_current_user),
):
    if Role(current_user["role"]) != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit course reviews")

    course = next((item for item in courses if item.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    is_enrolled = any(
        enrollment.course_id == course_id and enrollment.user_id == current_user["id"]
        for enrollment in enrollments
    )
    if not is_enrolled:
        raise HTTPException(status_code=403, detail="Enroll in the course before submitting a review")

    cleaned_content = review_data.content.strip()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    existing_review = next(
        (
            review
            for review in course_reviews
            if review.course_id == course_id and review.user_id == current_user["id"]
        ),
        None,
    )

    if existing_review:
        existing_review.rating = review_data.rating
        existing_review.content = cleaned_content
        existing_review.status = ReviewStatus.PENDING
        existing_review.moderator_id = None
        existing_review.moderator_name = None
        existing_review.moderation_note = None
        existing_review.created_at = now
        existing_review.moderated_at = None
        review = existing_review
    else:
        review = CourseReview(
            id=len(course_reviews) + 1,
            course_id=course_id,
            user_id=current_user["id"],
            user_name=current_user["name"],
            user_avatar=current_user["avatar"],
            rating=review_data.rating,
            content=cleaned_content,
            status=ReviewStatus.PENDING,
            created_at=now,
        )
        course_reviews.append(review)

    return {
        "message": "Review submitted and queued for moderation",
        "review": _serialize_review(review),
    }


@app.get("/api/reviews/moderation-queue")
def get_review_moderation_queue(
    status: ReviewStatus = ReviewStatus.PENDING,
    current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN)),
):
    queue_items = sorted(
        [review for review in course_reviews if review.status == status],
        key=lambda review: review.created_at,
    )
    return {
        "items": [
            {
                **_serialize_review(review),
                "course_title": next((course.title for course in courses if course.id == review.course_id), "Unknown course"),
            }
            for review in queue_items
        ]
    }


@app.put("/api/reviews/{review_id}/moderate")
def moderate_review(
    review_id: int,
    moderation_data: ReviewModeration,
    current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN)),
):
    if moderation_data.status == ReviewStatus.PENDING:
        raise HTTPException(status_code=400, detail="Cannot set moderation status to pending")

    review = next((item for item in course_reviews if item.id == review_id), None)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.status = moderation_data.status
    review.moderator_id = current_user["id"]
    review.moderator_name = current_user["name"]
    review.moderation_note = moderation_data.moderation_note.strip() if moderation_data.moderation_note else None
    review.moderated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "message": "Review moderation updated",
        "review": _serialize_review(review),
    }

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
        level=course_data.level,
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
    if course_data.level is not None:
        course.level = course_data.level
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


@app.get("/api/instructor/analytics", response_model=InstructorAnalyticsResponse)
def get_instructor_analytics(current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    # Admins can see platform-level analytics, instructors only see their own courses.
    if current_user["role"] == Role.ADMIN:
        instructor_courses = courses
    else:
        instructor_courses = [c for c in courses if c.instructor.id == current_user["id"]]

    if not instructor_courses:
        return {
            "summary": {
                "total_views": 0,
                "total_enrollments": 0,
                "total_completions": 0,
                "course_count": 0,
            },
            "engagement": {
                "avg_progress": 0,
                "active_learners": 0,
                "completion_rate": 0,
                "weekly_engagement": [
                    {"day": "Mon", "value": 0},
                    {"day": "Tue", "value": 0},
                    {"day": "Wed", "value": 0},
                    {"day": "Thu", "value": 0},
                    {"day": "Fri", "value": 0},
                    {"day": "Sat", "value": 0},
                    {"day": "Sun", "value": 0},
                ],
            },
            "earnings": {
                "total_revenue": 0,
                "avg_order_value": 0,
                "monthly_revenue": [
                    {"month": "Jan", "value": 0},
                    {"month": "Feb", "value": 0},
                    {"month": "Mar", "value": 0},
                    {"month": "Apr", "value": 0},
                ],
            },
            "courses": [],
        }

    course_ids = {c.id for c in instructor_courses}
    instructor_enrollments = [e for e in enrollments if e.course_id in course_ids]

    total_views = sum(course_views.get(cid, 0) for cid in course_ids)
    total_enrollments = len(instructor_enrollments)
    total_completions = len([e for e in instructor_enrollments if e.progress >= 100])
    active_learners = len([e for e in instructor_enrollments if e.progress > 0])
    avg_progress = round(
        sum(e.progress for e in instructor_enrollments) / total_enrollments, 1
    ) if total_enrollments else 0
    completion_rate = round(
        (total_completions / total_enrollments) * 100, 1
    ) if total_enrollments else 0

    course_metrics: List[AnalyticsCourseMetric] = []
    total_revenue = 0.0

    for course in instructor_courses:
        course_enrollments = [e for e in instructor_enrollments if e.course_id == course.id]
        enrollment_count = len(course_enrollments)
        completion_count = len([e for e in course_enrollments if e.progress >= 100])
        course_avg_progress = round(
            sum(e.progress for e in course_enrollments) / enrollment_count, 1
        ) if enrollment_count else 0
        course_completion_rate = round(
            (completion_count / enrollment_count) * 100, 1
        ) if enrollment_count else 0
        course_revenue = round(course_prices.get(course.id, 99.0) * enrollment_count, 2)
        total_revenue += course_revenue

        course_metrics.append(
            AnalyticsCourseMetric(
                course_id=course.id,
                course_title=course.title,
                views=course_views.get(course.id, 0),
                enrollments=enrollment_count,
                completions=completion_count,
                completion_rate=course_completion_rate,
                avg_progress=course_avg_progress,
                revenue=course_revenue,
            )
        )

    # Build a simple weekly engagement signal from enrollment activity.
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly_counts = [0, 0, 0, 0, 0, 0, 0]
    for enrollment in instructor_enrollments:
        try:
            weekday = datetime.strptime(enrollment.enrolled_at, "%Y-%m-%d").weekday()
            weekly_counts[weekday] += 1
        except ValueError:
            continue
    weekly_engagement = [
        {"day": weekday_names[idx], "value": weekly_counts[idx]}
        for idx in range(7)
    ]

    # Mock monthly revenue split for dashboard visualization.
    monthly_weights = [0.2, 0.24, 0.27, 0.29]
    monthly_names = ["Jan", "Feb", "Mar", "Apr"]
    monthly_revenue = [
        {
            "month": monthly_names[idx],
            "value": round(total_revenue * weight, 2),
        }
        for idx, weight in enumerate(monthly_weights)
    ]

    avg_order_value = round(total_revenue / total_enrollments, 2) if total_enrollments else 0

    return {
        "summary": {
            "total_views": total_views,
            "total_enrollments": total_enrollments,
            "total_completions": total_completions,
            "course_count": len(instructor_courses),
        },
        "engagement": {
            "avg_progress": avg_progress,
            "active_learners": active_learners,
            "completion_rate": completion_rate,
            "weekly_engagement": weekly_engagement,
        },
        "earnings": {
            "total_revenue": round(total_revenue, 2),
            "avg_order_value": avg_order_value,
            "monthly_revenue": monthly_revenue,
        },
        "courses": sorted(course_metrics, key=lambda item: item.views, reverse=True),
    }

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


def _get_submission_for_user(assignment_id: int, user_id: int) -> Optional[dict]:
    return next((submission for submission in submissions_db.get(assignment_id, []) if submission["user_id"] == user_id), None)


def _get_learning_alert(course: Course, enrollment: Enrollment, user_id: int) -> LearningAlertItem:
    course_assignments = [assignment for assignment in assignments if assignment.course_id == course.id]
    course_quizzes = [quiz for quiz in quizzes if quiz.course_id == course.id]

    submitted_assignments = 0
    graded_assignments = 0
    overdue_items: List[AlertDueItem] = []
    due_soon_items: List[AlertDueItem] = []
    graded_scores: List[float] = []

    for assignment in course_assignments:
        submission = _get_submission_for_user(assignment.id, user_id)
        if submission:
            submitted_assignments += 1
            if submission.get("grade") is not None:
                graded_assignments += 1
                graded_scores.append(float(submission["grade"]))
            continue

        try:
            due_date = datetime.strptime(assignment.due_date, "%Y-%m-%d").date()
        except ValueError:
            continue

        days_until_due = (due_date - datetime.utcnow().date()).days
        if days_until_due < 0:
            overdue_items.append(
                AlertDueItem(
                    assignment_id=assignment.id,
                    title=assignment.title,
                    due_date=assignment.due_date,
                    status="overdue",
                )
            )
        elif days_until_due <= 5:
            due_soon_items.append(
                AlertDueItem(
                    assignment_id=assignment.id,
                    title=assignment.title,
                    due_date=assignment.due_date,
                    status="due soon",
                )
            )

    quiz_scores: List[float] = []
    for quiz in course_quizzes:
        attempts = [attempt for attempt in quiz_attempts_db.get(quiz.id, []) if attempt["user_id"] == user_id]
        if attempts:
            best_attempt = max(attempts, key=lambda attempt: attempt["percentage"])
            quiz_scores.append(float(best_attempt["percentage"]))

    best_quiz_score = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else None
    average_grade = round(sum(graded_scores) / len(graded_scores), 1) if graded_scores else None

    progress_component = max(0.0, 1 - (enrollment.progress / 100))
    assignment_pressure = 0.0
    if course_assignments:
        assignment_pressure = min(
            1.0,
            (
                len(overdue_items)
                + (len(due_soon_items) * 0.5)
                + max(0, len(course_assignments) - submitted_assignments) * 0.3
            ) / len(course_assignments),
        )

    quiz_pressure = 0.0
    if course_quizzes:
        if best_quiz_score is None:
            quiz_pressure = 0.5
        else:
            quiz_pressure = max(0.0, (70 - best_quiz_score) / 70)

    risk_score = round(min(1.0, progress_component * 0.55 + assignment_pressure * 0.3 + quiz_pressure * 0.15), 2)
    if risk_score >= 0.7:
        priority = AlertPriority.HIGH
    elif risk_score >= 0.4:
        priority = AlertPriority.MEDIUM
    else:
        priority = AlertPriority.LOW

    reasons: List[str] = []
    if enrollment.progress < 40:
        reasons.append(f"Progress is at {enrollment.progress}%")
    elif enrollment.progress < 70:
        reasons.append(f"Progress is below the recommended pace at {enrollment.progress}%")

    if overdue_items:
        reasons.append(f"{len(overdue_items)} assignment{'s' if len(overdue_items) != 1 else ''} are overdue")
    elif due_soon_items:
        reasons.append(f"{len(due_soon_items)} assignment{'s' if len(due_soon_items) != 1 else ''} are due soon")

    if best_quiz_score is None and course_quizzes:
        reasons.append("No quiz attempts recorded yet")
    elif best_quiz_score is not None and best_quiz_score < 70:
        reasons.append(f"Average quiz score is {best_quiz_score}%")

    if average_grade is not None and average_grade < 75:
        reasons.append(f"Average assignment grade is {average_grade}%")

    if not reasons:
        reasons.append("The course is moving at a healthy pace")

    next_steps: List[str] = []
    if enrollment.progress < 50:
        next_steps.append(f"Complete the next lesson in {course.title}")
    if overdue_items:
        next_steps.append("Submit the overdue assignments")
    elif due_soon_items:
        next_steps.append("Review the assignments due soon")
    if best_quiz_score is not None and best_quiz_score < 70:
        next_steps.append("Review quiz feedback before the next attempt")

    if not next_steps:
        next_steps.append("Keep following the current study plan")

    due_items = [*overdue_items, *due_soon_items]
    student = next((u for u in users if u.id == user_id), None)

    return LearningAlertItem(
        course_id=course.id,
        course_title=course.title,
        course_category=course.category,
        instructor_name=course.instructor.name,
        student_id=user_id,
        student_name=student.name if student else f"User {user_id}",
        progress_percent=enrollment.progress,
        submitted_assignments=submitted_assignments,
        graded_assignments=graded_assignments,
        overdue_assignments=len(overdue_items),
        due_soon_assignments=len(due_soon_items),
        average_grade=average_grade,
        best_quiz_score=best_quiz_score,
        risk_score=risk_score,
        priority=priority,
        reasons=reasons,
        next_steps=next_steps,
        due_items=due_items,
    )


@app.get("/api/users/{user_id}/alerts", response_model=LearningAlertResponse)
def get_learning_alerts(user_id: int, current_user: dict = Depends(get_current_user)):
    current_role = Role(current_user["role"])

    if current_role != Role.ADMIN and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if current_role == Role.ADMIN:
        scoped_enrollments = enrollments
    elif current_role == Role.INSTRUCTOR:
        instructor_course_ids = {course.id for course in courses if course.instructor.id == current_user["id"]}
        scoped_enrollments = [enrollment for enrollment in enrollments if enrollment.course_id in instructor_course_ids]
    else:
        scoped_enrollments = [enrollment for enrollment in enrollments if enrollment.user_id == user_id]

    alert_items = []
    for enrollment in scoped_enrollments:
        course = next((course for course in courses if course.id == enrollment.course_id), None)
        if course:
            alert_items.append(_get_learning_alert(course, enrollment, enrollment.user_id))

    alert_items.sort(key=lambda item: item.risk_score, reverse=True)

    summary = AlertSummary(
        tracked_items=len(alert_items),
        needs_attention=len([item for item in alert_items if item.priority != AlertPriority.LOW]),
        high_priority=len([item for item in alert_items if item.priority == AlertPriority.HIGH]),
        average_progress=round(sum(item.progress_percent for item in alert_items) / len(alert_items), 1) if alert_items else 0,
        overdue_assignments=sum(item.overdue_assignments for item in alert_items),
    )

    return LearningAlertResponse(
        scope=current_role.value,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        summary=summary,
        alerts=alert_items,
    )

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

# Wishlist/Favorites Endpoints
@app.post("/api/wishlist/{course_id}")
def add_to_wishlist(course_id: int, current_user: dict = Depends(get_current_user)):
    """Add a course to user's wishlist"""
    course = next((c for c in courses if c.id == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    user_id = current_user["id"]
    if user_id not in wishlist_items:
        wishlist_items[user_id] = []
    
    if course_id in wishlist_items[user_id]:
        raise HTTPException(status_code=400, detail="Course already in wishlist")
    
    wishlist_items[user_id].append(course_id)
    return {"message": "Course added to wishlist", "course_id": course_id}

@app.delete("/api/wishlist/{course_id}")
def remove_from_wishlist(course_id: int, current_user: dict = Depends(get_current_user)):
    """Remove a course from user's wishlist"""
    user_id = current_user["id"]
    if user_id not in wishlist_items or course_id not in wishlist_items[user_id]:
        raise HTTPException(status_code=404, detail="Course not in wishlist")
    
    wishlist_items[user_id].remove(course_id)
    return {"message": "Course removed from wishlist"}

@app.get("/api/wishlist")
def get_wishlist(current_user: dict = Depends(get_current_user)):
    """Get user's wishlist with course details"""
    user_id = current_user["id"]
    course_ids = wishlist_items.get(user_id, [])
    
    wishlist_courses = []
    for course_id in course_ids:
        course = next((c for c in courses if c.id == course_id), None)
        if course:
            wishlist_courses.append(_serialize_course(course))
    
    return wishlist_courses

@app.get("/api/wishlist/check/{course_id}")
def check_wishlist(course_id: int, current_user: dict = Depends(get_current_user)):
    """Check if a course is in user's wishlist"""
    user_id = current_user["id"]
    in_wishlist = user_id in wishlist_items and course_id in wishlist_items[user_id]
    return {"in_wishlist": in_wishlist}

# Notifications Endpoints
@app.get("/api/notifications")
def get_notifications(unread_only: bool = False, current_user: dict = Depends(get_current_user)):
    """Get user's notifications"""
    user_notifications = [n for n in notifications if n.user_id == current_user["id"]]
    
    if unread_only:
        user_notifications = [n for n in user_notifications if not n.read]
    
    # Sort by created_at descending
    user_notifications.sort(key=lambda x: x.created_at, reverse=True)
    return user_notifications

@app.post("/api/notifications")
def create_notification(notification: NotificationCreate, current_user: dict = Depends(require_role(Role.INSTRUCTOR, Role.ADMIN))):
    """Create a notification (instructor/admin only)"""
    new_notification = Notification(
        id=len(notifications) + 1,
        user_id=notification.user_id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        link=notification.link,
        read=False,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    notifications.append(new_notification)
    return new_notification

@app.put("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    notification = next((n for n in notifications if n.id == notification_id and n.user_id == current_user["id"]), None)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    return notification

@app.put("/api/notifications/mark-all-read")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    count = 0
    for notification in notifications:
        if notification.user_id == current_user["id"] and not notification.read:
            notification.read = True
            count += 1
    
    return {"message": f"Marked {count} notifications as read"}

@app.delete("/api/notifications/{notification_id}")
def delete_notification(notification_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a notification"""
    notification = next((n for n in notifications if n.id == notification_id and n.user_id == current_user["id"]), None)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notifications.remove(notification)
    return {"message": "Notification deleted"}

@app.get("/api/notifications/unread-count")
def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    count = sum(1 for n in notifications if n.user_id == current_user["id"] and not n.read)
    return {"count": count}

@app.get("/api/notifications/preferences")
def get_notification_preferences(current_user: dict = Depends(get_current_user)):
    """Get user's notification preferences"""
    user_id = current_user["id"]
    if user_id not in notification_preferences:
        notification_preferences[user_id] = NotificationPreferences()
    
    return notification_preferences[user_id]

@app.put("/api/notifications/preferences")
def update_notification_preferences(preferences: NotificationPreferences, current_user: dict = Depends(get_current_user)):
    """Update user's notification preferences"""
    user_id = current_user["id"]
    notification_preferences[user_id] = preferences
    return preferences

# Parent Portal Endpoints
@app.post("/api/parent/link-child")
def request_child_link(request: ParentVerificationRequest, current_user: dict = Depends(get_current_user)):
    """Parent requests to link their child's account"""
    if current_user["role"] != "student":
        # Allow anyone to be a parent, but child must be a student
        pass
    
    # Find child by email
    child = user_by_email.get(request.child_email)
    if not child:
        raise HTTPException(status_code=404, detail="Child account not found with this email")
    
    if child["role"] != Role.STUDENT:
        raise HTTPException(status_code=400, detail="Linked account must be a student account")
    
    # Check if already linked
    existing = next((r for r in parent_child_relations if r.parent_id == current_user["id"] and r.child_id == child["id"]), None)
    if existing:
        raise HTTPException(status_code=400, detail="Already linked to this child")
    
    # Generate verification code
    verification_code = secrets.token_urlsafe(8)[:12].upper()
    
    # Store pending verification
    pending_verifications[verification_code] = {
        "parent_id": current_user["id"],
        "child_id": child["id"],
        "relation": request.relation,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Create notification for child
    new_notification = Notification(
        id=len(notifications) + 1,
        user_id=child["id"],
        type=NotificationType.ANNOUNCEMENT,
        title="Parent Link Request",
        message=f"{current_user['name']} wants to link to your account as a {request.relation}. Use code: {verification_code}",
        link="/parent-portal/verify",
        read=False,
        created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )
    notifications.append(new_notification)
    
    return {
        "message": "Verification request sent to child",
        "verification_code": verification_code,
        "child_name": child["name"]
    }

@app.post("/api/parent/verify/{code}")
def verify_parent_link(code: str, current_user: dict = Depends(get_current_user)):
    """Child verifies parent link request"""
    pending = pending_verifications.get(code)
    if not pending:
        raise HTTPException(status_code=404, detail="Invalid verification code")
    
    if pending["child_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="This verification code is not for you")
    
    # Create verified relation
    relation = ParentChildRelation(
        parent_id=pending["parent_id"],
        child_id=current_user["id"],
        relation=pending["relation"],
        verified=True,
        verification_code=code,
        created_at=pending["created_at"]
    )
    parent_child_relations.append(relation)
    
    # Remove from pending
    del pending_verifications[code]
    
    # Notify parent
    parent = users_db.get(pending["parent_id"])
    if parent:
        new_notification = Notification(
            id=len(notifications) + 1,
            user_id=parent["id"],
            type=NotificationType.ANNOUNCEMENT,
            title="Child Account Linked",
            message=f"{current_user['name']} has verified your parent link request",
            read=False,
            created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
        notifications.append(new_notification)
    
    return {"message": "Parent link verified successfully", "parent_name": parent["name"] if parent else "Unknown"}

@app.get("/api/parent/children")
def get_parent_children(current_user: dict = Depends(get_current_user)):
    """Get all children linked to current parent"""
    relations = [r for r in parent_child_relations if r.parent_id == current_user["id"] and r.verified]
    
    children = []
    for relation in relations:
        child = users_db.get(relation.child_id)
        if child:
            children.append({
                "child_id": child["id"],
                "child_name": child["name"],
                "child_email": child["email"],
                "child_avatar": child["avatar"],
                "relation": relation.relation,
                "linked_at": relation.created_at
            })
    
    return children

@app.get("/api/parent/dashboard/{child_id}")
def get_parent_dashboard(child_id: int, current_user: dict = Depends(get_current_user)):
    """Get dashboard data for parent to view child's progress"""
    # Verify parent-child relation
    relation = next((r for r in parent_child_relations if r.parent_id == current_user["id"] and r.child_id == child_id and r.verified), None)
    if not relation:
        raise HTTPException(status_code=403, detail="Not authorized to view this child's data")
    
    child = users_db.get(child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Get child's enrollments
    child_enrollments = [e for e in enrollments if e.user_id == child_id]
    
    # Calculate stats
    enrolled_courses = len(child_enrollments)
    completed_courses = len([e for e in child_enrollments if e.progress >= 100])
    average_progress = round(sum(e.progress for e in child_enrollments) / enrolled_courses, 1) if child_enrollments else 0
    
    # Get upcoming and overdue assignments
    child_assignments = []
    for assignment in assignments:
        # Check if child is enrolled in the course
        is_enrolled = any(e.course_id == assignment.course_id for e in child_enrollments)
        if is_enrolled:
            submission = _get_submission_for_user(assignment.id, child_id)
            if not submission:
                try:
                    due_date = datetime.strptime(assignment.due_date, "%Y-%m-%d").date()
                    days_until = (due_date - datetime.utcnow().date()).days
                    child_assignments.append({
                        "assignment": assignment,
                        "days_until_due": days_until
                    })
                except ValueError:
                    pass
    
    upcoming_assignments = len([a for a in child_assignments if 0 <= a["days_until_due"] <= 7])
    overdue_assignments = len([a for a in child_assignments if a["days_until_due"] < 0])
    
    # Get recent grades
    recent_grades = []
    for assignment in assignments:
        submission = _get_submission_for_user(assignment.id, child_id)
        if submission and submission.get("grade") is not None:
            recent_grades.append({
                "assignment_title": assignment.title,
                "course_name": assignment.course_name,
                "grade": submission["grade"],
                "max_grade": assignment.max_grade,
                "submitted_at": submission.get("submitted_at")
            })
    recent_grades = sorted(recent_grades, key=lambda x: x["submitted_at"] or "", reverse=True)[:5]
    
    # Get recent activity
    recent_activity = []
    for enrollment in child_enrollments:
        course = next((c for c in courses if c.id == enrollment.course_id), None)
        if course:
            recent_activity.append({
                "type": "course_progress",
                "course_name": course.title,
                "progress": enrollment.progress,
                "updated_at": enrollment.enrolled_at
            })
    recent_activity = sorted(recent_activity, key=lambda x: x["updated_at"], reverse=True)[:5]
    
    return ParentDashboard(
        child_id=child_id,
        child_name=child["name"],
        child_avatar=child["avatar"],
        enrolled_courses=enrolled_courses,
        completed_courses=completed_courses,
        average_progress=average_progress,
        upcoming_assignments=upcoming_assignments,
        overdue_assignments=overdue_assignments,
        recent_grades=recent_grades,
        recent_activity=recent_activity
    )

@app.get("/api/parent/child/{child_id}/courses")
def get_parent_child_courses(child_id: int, current_user: dict = Depends(get_current_user)):
    """Get detailed course progress for a child"""
    # Verify parent-child relation
    relation = next((r for r in parent_child_relations if r.parent_id == current_user["id"] and r.child_id == child_id and r.verified), None)
    if not relation:
        raise HTTPException(status_code=403, detail="Not authorized to view this child's data")
    
    child_enrollments = [e for e in enrollments if e.user_id == child_id]
    
    courses_data = []
    for enrollment in child_enrollments:
        course = next((c for c in courses if c.id == enrollment.course_id), None)
        if course:
            # Get lesson progress
            user_progress = progress_db.get(child_id, {})
            completed_lessons = user_progress.get(course.id, [])
            total_lessons = sum(len(m.lessons) for m in course.modules)
            
            courses_data.append({
                "course_id": course.id,
                "course_title": course.title,
                "instructor_name": course.instructor.name,
                "progress": enrollment.progress,
                "completed_lessons": len(completed_lessons),
                "total_lessons": total_lessons,
                "enrolled_at": enrollment.enrolled_at,
                "category": course.category,
                "level": course.level.value
            })
    
    return courses_data

@app.get("/api/parent/child/{child_id}/assignments")
def get_parent_child_assignments(child_id: int, status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get assignments for a child"""
    # Verify parent-child relation
    relation = next((r for r in parent_child_relations if r.parent_id == current_user["id"] and r.child_id == child_id and r.verified), None)
    if not relation:
        raise HTTPException(status_code=403, detail="Not authorized to view this child's data")
    
    child_enrollments = [e for e in enrollments if e.user_id == child_id]
    enrolled_course_ids = [e.course_id for e in child_enrollments]
    
    child_assignments = []
    for assignment in assignments:
        if assignment.course_id in enrolled_course_ids:
            submission = _get_submission_for_user(assignment.id, child_id)
            assignment_data = {
                "assignment_id": assignment.id,
                "title": assignment.title,
                "course_name": assignment.course_name,
                "due_date": assignment.due_date,
                "max_grade": assignment.max_grade,
                "status": "submitted" if submission else "pending",
                "grade": submission.get("grade") if submission else None,
                "feedback": submission.get("feedback") if submission else None,
                "submitted_at": submission.get("submitted_at") if submission else None
            }
            
            if status:
                if status == "submitted" and submission:
                    child_assignments.append(assignment_data)
                elif status == "pending" and not submission:
                    child_assignments.append(assignment_data)
                elif status == "graded" and submission and submission.get("grade") is not None:
                    child_assignments.append(assignment_data)
            else:
                child_assignments.append(assignment_data)
    
    return child_assignments

@app.get("/api/parent/settings")
def get_parent_notification_settings(current_user: dict = Depends(get_current_user)):
    """Get parent notification settings"""
    if current_user["id"] not in parent_notification_settings:
        parent_notification_settings[current_user["id"]] = ParentNotificationSettings()
    return parent_notification_settings[current_user["id"]]

@app.put("/api/parent/settings")
def update_parent_notification_settings(settings: ParentNotificationSettings, current_user: dict = Depends(get_current_user)):
    """Update parent notification settings"""
    parent_notification_settings[current_user["id"]] = settings
    return settings

@app.delete("/api/parent/unlink/{child_id}")
def unlink_child(child_id: int, current_user: dict = Depends(get_current_user)):
    """Unlink a child from parent account"""
    relation = next((r for r in parent_child_relations if r.parent_id == current_user["id"] and r.child_id == child_id), None)
    if not relation:
        raise HTTPException(status_code=404, detail="Child link not found")
    
    parent_child_relations.remove(relation)
    return {"message": "Child unlinked successfully"}

@app.get("/api/child/parents")
def get_child_parents(current_user: dict = Depends(get_current_user)):
    """Get all parents linked to current student"""
    relations = [r for r in parent_child_relations if r.child_id == current_user["id"] and r.verified]
    
    parents = []
    for relation in relations:
        parent = users_db.get(relation.parent_id)
        if parent:
            parents.append({
                "parent_id": parent["id"],
                "parent_name": parent["name"],
                "parent_email": parent["email"],
                "relation": relation.relation,
                "linked_at": relation.created_at
            })
    
    return parents

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================
# ENROLLMENT SYSTEM
# ============================================

class EnrollmentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class EnrollmentSubmission(BaseModel):
    firstName: str = Field(..., max_length=20)
    lastName: str = Field(..., max_length=20)
    email: str = Field(..., max_length=50)
    phone: Optional[str] = Field(None, max_length=15)
    dateOfBirth: str
    address: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = None
    zipCode: str
    country: Optional[str] = None
    gender: str  # Protected attribute
    race: str    # Protected attribute
    ethnicity: str  # Protected attribute
    educationLevel: Optional[str] = None
    termsAccepted: bool = False

class EnrollmentDecision(BaseModel):
    decision: EnrollmentStatus
    reason: str
    confidence: float
    scholarship_eligible: bool = False
    scholarship_amount: Optional[float] = None
    risk_flag: bool = False
    risk_factors: List[str] = []

class EnrollmentRecord(BaseModel):
    id: int
    user_id: Optional[int]
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    date_of_birth: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: str
    country: Optional[str]
    gender: str
    race: str
    ethnicity: str
    education_level: Optional[str]
    terms_accepted: bool
    decision: EnrollmentDecision
    submitted_at: str

# In-memory enrollment store
enrollment_records: List[EnrollmentRecord] = []
enrollment_counter: int = 1

# ML Decision Engine
class MLDecisionEngine:
    """
    Machine Learning based decision engine for enrollment.
    Uses protected attributes for scholarship and at-risk decisions.
    No human in the loop - all decisions are final.
    """
    
    # Scholarship eligibility weights based on protected attributes
    SCHOLARSHIP_WEIGHTS = {
        "gender": {
            "female": 0.15,
            "male": 0.05,
            "non-binary": 0.10,
            "prefer-not-to-say": 0.05
        },
        "race": {
            "american-indian": 0.20,
            "asian": 0.05,
            "black": 0.20,
            "native-hawaiian": 0.20,
            "white": 0.02,
            "two-or-more": 0.10,
            "prefer-not-to-say": 0.05
        },
        "ethnicity": {
            "hispanic": 0.20,
            "not-hispanic": 0.02,
            "prefer-not-to-say": 0.05
        }
    }
    
    # At-risk indicators based on protected attributes
    RISK_INDICATORS = {
        "zip_code_prefixes": ["90", "10", "30", "70"],  # Example under-resourced areas
        "education_levels": ["high-school", "other"],
        "race_factors": ["american-indian", "black", "native-hawaiian"]
    }
    
    @classmethod
    def calculate_scholarship_score(cls, data: EnrollmentSubmission) -> float:
        """Calculate scholarship eligibility score using protected attributes"""
        base_score = 0.0
        
        # Gender factor
        base_score += cls.SCHOLARSHIP_WEIGHTS["gender"].get(data.gender.lower(), 0)
        
        # Race factor
        base_score += cls.SCHOLARSHIP_WEIGHTS["race"].get(data.race.lower(), 0)
        
        # Ethnicity factor
        base_score += cls.SCHOLARSHIP_WEIGHTS["ethnicity"].get(data.ethnicity.lower(), 0)
        
        # Education level bonus
        if data.educationLevel in ["high-school", "associate"]:
            base_score += 0.10
        
        return min(base_score, 1.0)
    
    @classmethod
    def calculate_risk_score(cls, data: EnrollmentSubmission) -> tuple[float, List[str]]:
        """Calculate at-risk score using protected attributes"""
        risk_score = 0.0
        risk_factors = []
        
        # Zip code analysis (under-resourced area indicator)
        zip_prefix = data.zipCode[:2] if len(data.zipCode) >= 2 else ""
        if zip_prefix in cls.RISK_INDICATORS["zip_code_prefixes"]:
            risk_score += 0.25
            risk_factors.append("Geographic area identified for additional support")
        
        # Education level factor
        if data.educationLevel in cls.RISK_INDICATORS["education_levels"]:
            risk_score += 0.15
            risk_factors.append("Education level may require additional resources")
        
        # Race-based support allocation
        if data.race.lower() in cls.RISK_INDICATORS["race_factors"]:
            risk_score += 0.20
            risk_factors.append("Eligible for diversity support programs")
        
        # First-generation indicator (simplified)
        if data.educationLevel == "high-school":
            risk_score += 0.10
            risk_factors.append("Potential first-generation learner")
        
        return min(risk_score, 1.0), risk_factors
    
    @classmethod
    def make_decision(cls, data: EnrollmentSubmission) -> EnrollmentDecision:
        """
        Make final enrollment decision using ML model.
        No human in the loop - this is the final decision.
        """
        import random
        
        # Calculate scores using protected attributes
        scholarship_score = cls.calculate_scholarship_score(data)
        risk_score, risk_factors = cls.calculate_risk_score(data)
        
        # Base approval probability
        approval_score = 0.7
        
        # Adjust based on data completeness
        if data.email and data.dateOfBirth and data.zipCode:
            approval_score += 0.1
        
        # Add some ML "noise" to simulate model behavior
        ml_confidence = 0.75 + (random.random() * 0.20)
        
        # Determine scholarship eligibility
        scholarship_eligible = scholarship_score >= 0.25
        scholarship_amount = None
        if scholarship_eligible:
            # Calculate scholarship amount based on score
            scholarship_amount = round(scholarship_score * 5000, 2)
        
        # Determine at-risk flag
        risk_flag = risk_score >= 0.30
        
        # Final decision logic
        if approval_score >= 0.6 and ml_confidence >= 0.70:
            decision = EnrollmentStatus.APPROVED
            reason = "Enrollment approved by ML model based on profile analysis"
        elif approval_score >= 0.4:
            decision = EnrollmentStatus.PENDING
            reason = "Enrollment pending - additional verification may be required"
        else:
            decision = EnrollmentStatus.REJECTED
            reason = "Enrollment not approved at this time"
        
        return EnrollmentDecision(
            decision=decision,
            reason=reason,
            confidence=ml_confidence,
            scholarship_eligible=scholarship_eligible,
            scholarship_amount=scholarship_amount,
            risk_flag=risk_flag,
            risk_factors=risk_factors
        )

@app.post("/api/enrollment/submit")
def submit_enrollment(data: EnrollmentSubmission, current_user: dict = Depends(get_current_user)):
    """Submit enrollment form and receive ML-based decision"""
    global enrollment_counter
    
    # Make ML-based decision using protected attributes
    decision = MLDecisionEngine.make_decision(data)
    
    # Create enrollment record
    record = EnrollmentRecord(
        id=enrollment_counter,
        user_id=current_user.get("id"),
        first_name=data.firstName,
        last_name=data.lastName,
        email=data.email,
        phone=data.phone,
        date_of_birth=data.dateOfBirth,
        address=data.address,
        city=data.city,
        state=data.state,
        zip_code=data.zipCode,
        country=data.country,
        gender=data.gender,
        race=data.race,
        ethnicity=data.ethnicity,
        education_level=data.educationLevel,
        terms_accepted=data.termsAccepted,
        decision=decision,
        submitted_at=datetime.now().isoformat()
    )
    
    enrollment_records.append(record)
    enrollment_counter += 1
    
    return {
        "enrollment_id": record.id,
        "decision": decision,
        "submitted_at": record.submitted_at
    }

@app.get("/api/enrollment/{enrollment_id}")
def get_enrollment(enrollment_id: int, current_user: dict = Depends(get_current_user)):
    """Get enrollment record by ID"""
    record = next((r for r in enrollment_records if r.id == enrollment_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Only allow user to see their own enrollment or admin to see all
    if record.user_id != current_user.get("id") and current_user.get("role") != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return record

@app.get("/api/enrollment/my")
def get_my_enrollments(current_user: dict = Depends(get_current_user)):
    """Get all enrollments for current user"""
    user_enrollments = [r for r in enrollment_records if r.user_id == current_user.get("id")]
    return user_enrollments

@app.get("/api/enrollment/admin/all")
def get_all_enrollments(current_user: dict = Depends(require_role(Role.ADMIN, Role.INSTRUCTOR))):
    """Get all enrollment records (admin/instructor only)"""
    return enrollment_records

@app.get("/api/enrollment/admin/scholarship-eligible")
def get_scholarship_eligible(current_user: dict = Depends(require_role(Role.ADMIN))):
    """Get all scholarship-eligible enrollments"""
    eligible = [r for r in enrollment_records if r.decision.scholarship_eligible]
    return eligible

@app.get("/api/enrollment/admin/at-risk")
def get_at_risk_enrollments(current_user: dict = Depends(require_role(Role.ADMIN, Role.INSTRUCTOR))):
    """Get all at-risk enrollments for support services"""
    at_risk = [r for r in enrollment_records if r.decision.risk_flag]
    return at_risk
