from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id            = Column(String, primary_key=True, default=gen_uuid)
    name          = Column(String(255), nullable=False)
    email         = Column(String(255), unique=True, nullable=False)
    password      = Column(String(255), nullable=False)
    role          = Column(String(20), default="student")   # admin/faculty/student
    student_type  = Column(String(20), nullable=True)       # school/college
    class_grade   = Column(String(50), nullable=True)
    avatar        = Column(String(500), nullable=True)
    bio           = Column(Text, nullable=True)
    phone         = Column(String(20), nullable=True)
    is_verified   = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    two_fa_secret = Column(String(255), nullable=True)
    two_fa_enabled= Column(Boolean, default=False)
    refresh_token = Column(Text, nullable=True)
    last_login    = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    courses       = relationship("Course", back_populates="faculty")
    enrollments   = relationship("Enrollment", back_populates="student")
    points        = relationship("UserPoints", back_populates="user", uselist=False)

class Course(Base):
    __tablename__ = "courses"
    id             = Column(String, primary_key=True, default=gen_uuid)
    title          = Column(String(500), nullable=False)
    description    = Column(Text)
    category       = Column(String(100))
    subcategory    = Column(String(100))
    level          = Column(String(20), default="beginner")
    price          = Column(Float, default=0)
    thumbnail      = Column(String(500))
    faculty_id     = Column(String, ForeignKey("users.id"))
    student_type   = Column(String(20))
    class_grade    = Column(String(50))
    language       = Column(String(50), default="English")
    duration_hours = Column(Integer, default=0)
    is_published   = Column(Boolean, default=False)
    is_featured    = Column(Boolean, default=False)
    rating         = Column(Float, default=0)
    total_students = Column(Integer, default=0)
    tags           = Column(JSON, default=list)
    created_at     = Column(DateTime, server_default=func.now())
    updated_at     = Column(DateTime, server_default=func.now(), onupdate=func.now())

    faculty        = relationship("User", back_populates="courses")
    enrollments    = relationship("Enrollment", back_populates="course")
    lectures       = relationship("Lecture", back_populates="course")
    quizzes        = relationship("Quiz", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id           = Column(String, primary_key=True, default=gen_uuid)
    student_id   = Column(String, ForeignKey("users.id"))
    course_id    = Column(String, ForeignKey("courses.id"))
    progress     = Column(Integer, default=0)
    completed    = Column(Boolean, default=False)
    enrolled_at  = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    student      = relationship("User", back_populates="enrollments")
    course       = relationship("Course", back_populates="enrollments")

class Lecture(Base):
    __tablename__ = "lectures"
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("courses.id"))
    title       = Column(String(500), nullable=False)
    description = Column(Text)
    video_url   = Column(String(500))
    duration    = Column(Integer, default=0)
    order_index = Column(Integer, default=0)
    is_preview  = Column(Boolean, default=False)
    resources   = Column(JSON, default=list)
    ai_summary  = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())

    course      = relationship("Course", back_populates="lectures")

class Quiz(Base):
    __tablename__ = "quizzes"
    id            = Column(String, primary_key=True, default=gen_uuid)
    course_id     = Column(String, ForeignKey("courses.id"))
    title         = Column(String(500), nullable=False)
    description   = Column(Text)
    time_limit    = Column(Integer, default=30)
    passing_score = Column(Integer, default=60)
    max_attempts  = Column(Integer, default=3)
    is_published  = Column(Boolean, default=True)
    created_at    = Column(DateTime, server_default=func.now())

    course        = relationship("Course", back_populates="quizzes")
    questions     = relationship("QuizQuestion", back_populates="quiz")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id             = Column(String, primary_key=True, default=gen_uuid)
    quiz_id        = Column(String, ForeignKey("quizzes.id"))
    question       = Column(Text, nullable=False)
    type           = Column(String(20), default="mcq")
    options        = Column(JSON)
    correct_answer = Column(Text)
    explanation    = Column(Text)
    marks          = Column(Integer, default=1)
    order_index    = Column(Integer, default=0)

    quiz           = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id           = Column(String, primary_key=True, default=gen_uuid)
    quiz_id      = Column(String, ForeignKey("quizzes.id"))
    student_id   = Column(String, ForeignKey("users.id"))
    answers      = Column(JSON)
    score        = Column(Integer)
    passed       = Column(Boolean)
    time_taken   = Column(Integer)
    attempted_at = Column(DateTime, server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id          = Column(String, primary_key=True, default=gen_uuid)
    sender_id   = Column(String, ForeignKey("users.id"))
    receiver_id = Column(String, ForeignKey("users.id"), nullable=True)
    course_id   = Column(String, ForeignKey("courses.id"), nullable=True)
    content     = Column(Text)
    type        = Column(String(20), default="text")
    file_url    = Column(String(500))
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id         = Column(String, primary_key=True, default=gen_uuid)
    user_id    = Column(String, ForeignKey("users.id"))
    title      = Column(String(255))
    message    = Column(Text)
    type       = Column(String(50))
    data       = Column(JSON)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class Certificate(Base):
    __tablename__ = "certificates"
    id              = Column(String, primary_key=True, default=gen_uuid)
    student_id      = Column(String, ForeignKey("users.id"))
    course_id       = Column(String, ForeignKey("courses.id"))
    certificate_url = Column(String(500))
    issued_at       = Column(DateTime, server_default=func.now())

class Review(Base):
    __tablename__ = "reviews"
    id         = Column(String, primary_key=True, default=gen_uuid)
    course_id  = Column(String, ForeignKey("courses.id"))
    student_id = Column(String, ForeignKey("users.id"))
    rating     = Column(Integer)
    comment    = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class UserPoints(Base):
    __tablename__ = "user_points"
    id            = Column(String, primary_key=True, default=gen_uuid)
    user_id       = Column(String, ForeignKey("users.id"), unique=True)
    xp            = Column(Integer, default=0)
    level         = Column(Integer, default=1)
    streak_days   = Column(Integer, default=0)
    last_activity = Column(String, nullable=True)
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user          = relationship("User", back_populates="points")

class Badge(Base):
    __tablename__ = "badges"
    id              = Column(String, primary_key=True, default=gen_uuid)
    name            = Column(String(100))
    description     = Column(Text)
    icon            = Column(String(10))
    condition_type  = Column(String(50))
    condition_value = Column(Integer)

class UserBadge(Base):
    __tablename__ = "user_badges"
    id        = Column(String, primary_key=True, default=gen_uuid)
    user_id   = Column(String, ForeignKey("users.id"))
    badge_id  = Column(String, ForeignKey("badges.id"))
    earned_at = Column(DateTime, server_default=func.now())

class StudyPlan(Base):
    __tablename__ = "study_plans"
    id           = Column(String, primary_key=True, default=gen_uuid)
    student_id   = Column(String, ForeignKey("users.id"))
    title        = Column(String(255))
    goal         = Column(Text)
    start_date   = Column(String)
    end_date     = Column(String)
    schedule     = Column(JSON)
    ai_generated = Column(Boolean, default=False)
    created_at   = Column(DateTime, server_default=func.now())

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id         = Column(String, primary_key=True, default=gen_uuid)
    user_id    = Column(String, ForeignKey("users.id"))
    messages   = Column(JSON, default=list)
    topic      = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Assignment(Base):
    __tablename__ = "assignments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("courses.id"))
    faculty_id  = Column(String, ForeignKey("users.id"))
    title       = Column(String(500))
    description = Column(Text)
    due_date    = Column(DateTime)
    max_marks   = Column(Integer, default=100)
    created_at  = Column(DateTime, server_default=func.now())

class Internship(Base):
    __tablename__ = "internships"
    id           = Column(String, primary_key=True, default=gen_uuid)
    title        = Column(String(500))
    company      = Column(String(255))
    description  = Column(Text)
    location     = Column(String(255))
    type         = Column(String(20))
    stipend      = Column(String(100))
    apply_url    = Column(String(500))
    deadline     = Column(String)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, server_default=func.now())

class LiveClass(Base):
    __tablename__ = "live_classes"
    id               = Column(String, primary_key=True, default=gen_uuid)
    course_id        = Column(String, ForeignKey("courses.id"))
    faculty_id       = Column(String, ForeignKey("users.id"))
    title            = Column(String(500))
    description      = Column(Text)
    scheduled_at     = Column(DateTime)
    duration_minutes = Column(Integer, default=60)
    meeting_url      = Column(String(500))
    status           = Column(String(20), default="scheduled")
    created_at       = Column(DateTime, server_default=func.now())
