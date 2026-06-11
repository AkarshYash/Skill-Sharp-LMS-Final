from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
import enum

def gen_uuid():
    return str(uuid.uuid4())

# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────
class UserRole(str, enum.Enum):
    admin = "admin"
    faculty = "faculty"
    student = "student"

class CourseLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class LiveClassStatus(str, enum.Enum):
    scheduled = "scheduled"
    live = "live"
    completed = "completed"
    cancelled = "cancelled"

# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id             = Column(String, primary_key=True, default=gen_uuid)
    name           = Column(String(255), nullable=False)
    email          = Column(String(255), unique=True, nullable=False)
    password       = Column(String(255), nullable=False)
    role           = Column(String(20), default="student")   # admin/faculty/student
    student_type   = Column(String(20), nullable=True)       # school/college/professional
    class_grade    = Column(String(50), nullable=True)
    avatar         = Column(String(500), nullable=True)
    bio            = Column(Text, nullable=True)
    phone          = Column(String(20), nullable=True)
    expertise      = Column(String(500), nullable=True)      # For faculty
    linkedin_url   = Column(String(500), nullable=True)
    github_url     = Column(String(500), nullable=True)
    is_verified    = Column(Boolean, default=False)
    is_active      = Column(Boolean, default=True)
    two_fa_secret  = Column(String(255), nullable=True)
    two_fa_enabled = Column(Boolean, default=False)
    refresh_token  = Column(Text, nullable=True)
    last_login     = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, server_default=func.now())
    updated_at     = Column(DateTime, server_default=func.now(), onupdate=func.now())

    courses        = relationship("Course", back_populates="faculty", foreign_keys="Course.faculty_id")
    enrollments    = relationship("Enrollment", back_populates="student")
    points         = relationship("UserPoints", back_populates="user", uselist=False)
    submissions    = relationship("AssignmentSubmission", back_populates="student", foreign_keys="AssignmentSubmission.student_id")
    ai_sessions    = relationship("AITutorSession", back_populates="user")

# ─────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"
    id              = Column(String, primary_key=True, default=gen_uuid)
    title           = Column(String(500), nullable=False)
    description     = Column(Text)
    short_desc      = Column(String(500))
    category        = Column(String(100))
    subcategory     = Column(String(100))
    level           = Column(String(20), default="beginner")
    price           = Column(Float, default=0)
    thumbnail       = Column(String(500))
    promo_video_url = Column(String(500))
    faculty_id      = Column(String, ForeignKey("users.id"))
    student_type    = Column(String(20))
    class_grade     = Column(String(50))
    language        = Column(String(50), default="English")
    duration_hours  = Column(Integer, default=0)
    is_published    = Column(Boolean, default=False)
    is_featured     = Column(Boolean, default=False)
    approval_status = Column(String(20), default="pending")   # pending/approved/rejected
    approval_note   = Column(Text, nullable=True)
    rating          = Column(Float, default=0)
    total_students  = Column(Integer, default=0)
    total_lectures  = Column(Integer, default=0)
    tags            = Column(JSON, default=list)
    what_you_learn  = Column(JSON, default=list)   # bullet points
    requirements    = Column(JSON, default=list)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    faculty         = relationship("User", back_populates="courses", foreign_keys=[faculty_id])
    enrollments     = relationship("Enrollment", back_populates="course")
    lectures        = relationship("Lecture", back_populates="course")
    quizzes         = relationship("Quiz", back_populates="course")
    assignments     = relationship("Assignment", back_populates="course")
    live_classes    = relationship("LiveClass", back_populates="course")
    reviews         = relationship("Review", back_populates="course")

# ─────────────────────────────────────────────
# ENROLLMENT
# ─────────────────────────────────────────────
class Enrollment(Base):
    __tablename__ = "enrollments"
    id           = Column(String, primary_key=True, default=gen_uuid)
    student_id   = Column(String, ForeignKey("users.id"))
    course_id    = Column(String, ForeignKey("courses.id"))
    progress     = Column(Integer, default=0)
    completed    = Column(Boolean, default=False)
    last_watched = Column(String, nullable=True)   # lecture_id
    payment_id   = Column(String, nullable=True)
    enrolled_at  = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    student      = relationship("User", back_populates="enrollments")
    course       = relationship("Course", back_populates="enrollments")

# ─────────────────────────────────────────────
# LECTURE
# ─────────────────────────────────────────────
class Lecture(Base):
    __tablename__ = "lectures"
    id             = Column(String, primary_key=True, default=gen_uuid)
    course_id      = Column(String, ForeignKey("courses.id"))
    title          = Column(String(500), nullable=False)
    description    = Column(Text)
    video_url      = Column(String(500))        # YouTube/Vimeo/direct link
    video_type     = Column(String(20), default="youtube")  # youtube/vimeo/upload/zoom
    duration       = Column(Integer, default=0) # seconds
    order_index    = Column(Integer, default=0)
    is_preview     = Column(Boolean, default=False)
    is_published   = Column(Boolean, default=True)
    resources      = Column(JSON, default=list)  # [{name, url, type}]
    ai_summary     = Column(Text)
    transcript     = Column(Text)
    created_at     = Column(DateTime, server_default=func.now())

    course         = relationship("Course", back_populates="lectures")
    notes          = relationship("LectureNote", back_populates="lecture")
    progress       = relationship("LectureProgress", back_populates="lecture")

# ─────────────────────────────────────────────
# LECTURE NOTES (uploaded PDFs for RAG)
# ─────────────────────────────────────────────
class LectureNote(Base):
    __tablename__ = "lecture_notes"
    id             = Column(String, primary_key=True, default=gen_uuid)
    lecture_id     = Column(String, ForeignKey("lectures.id"))
    course_id      = Column(String, ForeignKey("courses.id"))
    faculty_id     = Column(String, ForeignKey("users.id"))
    filename       = Column(String(500))
    file_url       = Column(String(500))
    file_type      = Column(String(50))   # pdf/doc/txt
    file_size      = Column(Integer)
    is_indexed     = Column(Boolean, default=False)  # RAG indexed
    vector_ids     = Column(JSON, default=list)      # ChromaDB doc IDs
    created_at     = Column(DateTime, server_default=func.now())

    lecture        = relationship("Lecture", back_populates="notes")

# ─────────────────────────────────────────────
# LECTURE PROGRESS
# ─────────────────────────────────────────────
class LectureProgress(Base):
    __tablename__ = "lecture_progress"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    lecture_id  = Column(String, ForeignKey("lectures.id"))
    course_id   = Column(String, ForeignKey("courses.id"))
    watched_sec = Column(Integer, default=0)
    completed   = Column(Boolean, default=False)
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    lecture     = relationship("Lecture", back_populates="progress")

# ─────────────────────────────────────────────
# QUIZ
# ─────────────────────────────────────────────
class Quiz(Base):
    __tablename__ = "quizzes"
    id            = Column(String, primary_key=True, default=gen_uuid)
    course_id     = Column(String, ForeignKey("courses.id"))
    lecture_id    = Column(String, ForeignKey("lectures.id"), nullable=True)
    title         = Column(String(500), nullable=False)
    description   = Column(Text)
    time_limit    = Column(Integer, default=30)   # minutes
    passing_score = Column(Integer, default=60)   # percent
    max_attempts  = Column(Integer, default=3)
    is_published  = Column(Boolean, default=True)
    ai_generated  = Column(Boolean, default=False)
    created_at    = Column(DateTime, server_default=func.now())

    course        = relationship("Course", back_populates="quizzes")
    questions     = relationship("QuizQuestion", back_populates="quiz")
    attempts      = relationship("QuizAttempt", back_populates="quiz")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id             = Column(String, primary_key=True, default=gen_uuid)
    quiz_id        = Column(String, ForeignKey("quizzes.id"))
    question       = Column(Text, nullable=False)
    type           = Column(String(20), default="mcq")  # mcq/true_false/short_answer
    options        = Column(JSON)                        # ["A", "B", "C", "D"]
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
    max_score    = Column(Integer)
    passed       = Column(Boolean)
    time_taken   = Column(Integer)  # seconds
    ai_feedback  = Column(Text)     # AI-generated feedback
    attempted_at = Column(DateTime, server_default=func.now())

    quiz         = relationship("Quiz", back_populates="attempts")

# ─────────────────────────────────────────────
# ASSIGNMENT
# ─────────────────────────────────────────────
class Assignment(Base):
    __tablename__ = "assignments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("courses.id"))
    faculty_id  = Column(String, ForeignKey("users.id"))
    title       = Column(String(500))
    description = Column(Text)
    due_date    = Column(DateTime)
    max_marks   = Column(Integer, default=100)
    allow_late  = Column(Boolean, default=False)
    file_url    = Column(String(500))    # assignment brief doc
    created_at  = Column(DateTime, server_default=func.now())

    course      = relationship("Course", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    id           = Column(String, primary_key=True, default=gen_uuid)
    assignment_id= Column(String, ForeignKey("assignments.id"))
    student_id   = Column(String, ForeignKey("users.id"))
    content      = Column(Text)
    file_url     = Column(String(500))
    marks        = Column(Integer, nullable=True)
    feedback     = Column(Text, nullable=True)
    ai_feedback  = Column(Text, nullable=True)
    graded_by    = Column(String, ForeignKey("users.id"), nullable=True)
    is_late      = Column(Boolean, default=False)
    submitted_at = Column(DateTime, server_default=func.now())
    graded_at    = Column(DateTime, nullable=True)

    assignment   = relationship("Assignment", back_populates="submissions")
    student      = relationship("User", back_populates="submissions", foreign_keys=[student_id])

# ─────────────────────────────────────────────
# MESSAGING
# ─────────────────────────────────────────────
class Message(Base):
    __tablename__ = "messages"
    id          = Column(String, primary_key=True, default=gen_uuid)
    sender_id   = Column(String, ForeignKey("users.id"))
    receiver_id = Column(String, ForeignKey("users.id"), nullable=True)
    course_id   = Column(String, ForeignKey("courses.id"), nullable=True)  # course chat
    content     = Column(Text)
    type        = Column(String(20), default="text")   # text/file/image
    file_url    = Column(String(500))
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"
    id         = Column(String, primary_key=True, default=gen_uuid)
    user_id    = Column(String, ForeignKey("users.id"))
    title      = Column(String(255))
    message    = Column(Text)
    type       = Column(String(50))   # course/quiz/assignment/system/ai
    data       = Column(JSON)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

# ═════════════════════════════════════════════
# SKILL SHARP 365 - NEW COMPREHENSIVE MODULES
# ═════════════════════════════════════════════

# ─────────────────────────────────────────────
# 1. SCHOOL EDUCATION MODULE
# ─────────────────────────────────────────────
class SchoolClass(Base):
    """Represents Class 1 through Class 12"""
    __tablename__ = "school_classes"
    id          = Column(String, primary_key=True, default=gen_uuid)
    class_number = Column(Integer, nullable=False)  # 1-12
    section     = Column(String(10), nullable=True)  # A, B, C
    institution_id = Column(String, ForeignKey("institutions.id"))
    class_teacher_id = Column(String, ForeignKey("users.id"), nullable=True)
    max_students = Column(Integer, default=40)
    academic_year = Column(String(10))  # 2024-2025
    description = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())
    
    school_subjects = relationship("SchoolSubject", back_populates="school_class")
    students    = relationship("ClassEnrollment", back_populates="school_class")

class SchoolSubject(Base):
    """Subjects for each school class (Math, Science, English, etc.)"""
    __tablename__ = "school_subjects"
    id          = Column(String, primary_key=True, default=gen_uuid)
    school_class_id = Column(String, ForeignKey("school_classes.id"))
    name        = Column(String(100))  # Mathematics, Physics, Chemistry, etc.
    code        = Column(String(50))
    faculty_id  = Column(String, ForeignKey("users.id"))
    description = Column(Text)
    curriculum = Column(JSON)  # {chapters: []}
    created_at  = Column(DateTime, server_default=func.now())
    
    school_class = relationship("SchoolClass", back_populates="school_subjects")
    chapters    = relationship("SchoolChapter", back_populates="subject")
    materials   = relationship("SubjectMaterial", back_populates="subject")

class SchoolChapter(Base):
    """Chapters within each subject"""
    __tablename__ = "school_chapters"
    id          = Column(String, primary_key=True, default=gen_uuid)
    subject_id  = Column(String, ForeignKey("school_subjects.id"))
    chapter_num = Column(Integer)
    title       = Column(String(255))
    description = Column(Text)
    order_index = Column(Integer)
    created_at  = Column(DateTime, server_default=func.now())
    
    subject     = relationship("SchoolSubject", back_populates="chapters")
    topics      = relationship("SchoolTopic", back_populates="chapter")

class SchoolTopic(Base):
    """Topics within chapters"""
    __tablename__ = "school_topics"
    id          = Column(String, primary_key=True, default=gen_uuid)
    chapter_id  = Column(String, ForeignKey("school_chapters.id"))
    title       = Column(String(255))
    content     = Column(Text)
    order_index = Column(Integer)
    
    chapter     = relationship("SchoolChapter", back_populates="topics")

class SubjectMaterial(Base):
    """Notes, PDFs, Videos, Resources for subjects"""
    __tablename__ = "subject_materials"
    id          = Column(String, primary_key=True, default=gen_uuid)
    subject_id  = Column(String, ForeignKey("school_subjects.id"))
    title       = Column(String(255))
    material_type = Column(String(50))  # notes/pdf/video/youtube/document
    url         = Column(String(500), nullable=True)
    file_path   = Column(String(500), nullable=True)
    description = Column(Text)
    uploaded_by = Column(String, ForeignKey("users.id"))
    views       = Column(Integer, default=0)
    is_ai_generated = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())
    
    subject     = relationship("SchoolSubject", back_populates="materials")

class ClassEnrollment(Base):
    """Student enrollment in school classes"""
    __tablename__ = "class_enrollments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    school_class_id = Column(String, ForeignKey("school_classes.id"))
    roll_number = Column(String(50))
    enrollment_date = Column(DateTime, server_default=func.now())
    status      = Column(String(20), default="active")  # active/inactive/graduated
    
    student     = relationship("User")
    school_class = relationship("SchoolClass", back_populates="students")

class SchoolAttendance(Base):
    """Attendance for school classes"""
    __tablename__ = "school_attendance"
    id          = Column(String, primary_key=True, default=gen_uuid)
    school_class_id = Column(String, ForeignKey("school_classes.id"))
    subject_id  = Column(String, ForeignKey("school_subjects.id"))
    student_id  = Column(String, ForeignKey("users.id"))
    date        = Column(DateTime)
    status      = Column(String(20))  # present/absent/leave
    marked_by   = Column(String, ForeignKey("users.id"))
    created_at  = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# 2. COLLEGE EDUCATION MODULE
# ─────────────────────────────────────────────
class EducationStream(Base):
    """Education streams: Science, Commerce, Arts, Law, Medical"""
    __tablename__ = "education_streams"
    id          = Column(String, primary_key=True, default=gen_uuid)
    name        = Column(String(100))  # Science, Commerce, Arts, Law
    description = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())
    
    programs    = relationship("DegreeProgram", back_populates="stream")

class DegreeProgram(Base):
    """Degree Programs like BTech CSE, BCA, MBA, etc."""
    __tablename__ = "degree_programs"
    id          = Column(String, primary_key=True, default=gen_uuid)
    stream_id   = Column(String, ForeignKey("education_streams.id"))
    name        = Column(String(255))  # e.g., "BTech Computer Science"
    code        = Column(String(50))
    duration_years = Column(Integer)
    total_semesters = Column(Integer)
    description = Column(Text)
    specializations = Column(JSON, default=list)  # e.g., ["AI", "Web Dev", "Data Science"]
    created_at  = Column(DateTime, server_default=func.now())
    
    stream      = relationship("EducationStream", back_populates="programs")
    semesters   = relationship("Semester", back_populates="program")
    enrollments = relationship("ProgramEnrollment", back_populates="program")

class Semester(Base):
    """Semesters within degree programs"""
    __tablename__ = "semesters"
    id          = Column(String, primary_key=True, default=gen_uuid)
    program_id  = Column(String, ForeignKey("degree_programs.id"))
    semester_num = Column(Integer)  # 1-8
    title       = Column(String(100))
    description = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())
    
    program     = relationship("DegreeProgram", back_populates="semesters")
    subjects    = relationship("CollegeCourseSubject", back_populates="semester")

class CollegeCourseSubject(Base):
    """Subjects in college semesters"""
    __tablename__ = "college_course_subjects"
    id          = Column(String, primary_key=True, default=gen_uuid)
    semester_id = Column(String, ForeignKey("semesters.id"))
    code        = Column(String(50))
    name        = Column(String(255))
    credits     = Column(Integer, default=4)
    faculty_id  = Column(String, ForeignKey("users.id"), nullable=True)
    description = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())
    
    semester    = relationship("Semester", back_populates="subjects")
    materials   = relationship("CollegeMaterial", back_populates="subject")
    lectures    = relationship("CollegeLecture", back_populates="subject")

class CollegeMaterial(Base):
    """Notes, Books, PDFs for college subjects"""
    __tablename__ = "college_materials"
    id          = Column(String, primary_key=True, default=gen_uuid)
    subject_id  = Column(String, ForeignKey("college_course_subjects.id"))
    title       = Column(String(255))
    material_type = Column(String(50))  # notes/book/pdf/video/lab
    url         = Column(String(500), nullable=True)
    file_path   = Column(String(500), nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"))
    views       = Column(Integer, default=0)
    created_at  = Column(DateTime, server_default=func.now())
    
    subject     = relationship("CollegeCourseSubject", back_populates="materials")

class CollegeLecture(Base):
    """College lectures"""
    __tablename__ = "college_lectures"
    id          = Column(String, primary_key=True, default=gen_uuid)
    subject_id  = Column(String, ForeignKey("college_course_subjects.id"))
    title       = Column(String(255))
    description = Column(Text)
    video_url   = Column(String(500))
    duration    = Column(Integer)  # seconds
    transcript  = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())
    
    subject     = relationship("CollegeCourseSubject", back_populates="lectures")

class ProgramEnrollment(Base):
    """Student enrollment in college programs"""
    __tablename__ = "program_enrollments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    program_id  = Column(String, ForeignKey("degree_programs.id"))
    enrollment_year = Column(Integer)
    current_semester = Column(Integer)
    admission_number = Column(String(50))
    specialization = Column(String(100), nullable=True)
    gpa         = Column(Float, default=0.0)
    status      = Column(String(20), default="active")  # active/graduated/dropped
    enrolled_at = Column(DateTime, server_default=func.now())
    
    student     = relationship("User")
    program     = relationship("DegreeProgram", back_populates="enrollments")

# ─────────────────────────────────────────────
# 3. LIVE CLASSES SYSTEM
# ─────────────────────────────────────────────
class OldLiveClass(Base):
    """Live class sessions"""
    __tablename__ = "old_live_classes"
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("courses.id"))
    school_class_id = Column(String, ForeignKey("school_classes.id"), nullable=True)
    subject_id  = Column(String, ForeignKey("school_subjects.id"), nullable=True)
    faculty_id  = Column(String, ForeignKey("users.id"))
    title       = Column(String(255))
    description = Column(Text)
    scheduled_time = Column(DateTime)
    duration    = Column(Integer)  # minutes
    platform    = Column(String(50))  # zoom/google_meet/teams/jitsi/webrtc
    meeting_link = Column(String(500))
    meeting_id  = Column(String(255))
    passcode    = Column(String(255), nullable=True)
    status      = Column(String(20), default="scheduled")  # scheduled/live/completed/cancelled
    recording_url = Column(String(500), nullable=True)
    notes_url   = Column(String(500), nullable=True)
    max_attendees = Column(Integer, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    
    course      = relationship("Course")
    participants = relationship("LiveClassParticipant", back_populates="live_class")
    assignments = relationship("LiveClassAssignment", back_populates="live_class")

class LiveClassParticipant(Base):
    """Participants in live classes"""
    __tablename__ = "live_class_participants"
    id          = Column(String, primary_key=True, default=gen_uuid)
    live_class_id = Column(String, ForeignKey("old_live_classes.id"))
    student_id  = Column(String, ForeignKey("users.id"))
    joined_at   = Column(DateTime)
    left_at     = Column(DateTime, nullable=True)
    duration_attended = Column(Integer)  # seconds
    raised_hand = Column(Boolean, default=False)
    asked_question = Column(Boolean, default=False)
    
    live_class  = relationship("OldLiveClass", back_populates="participants")

class LiveClassAssignment(Base):
    """Assignments given during live classes"""
    __tablename__ = "live_class_assignments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    live_class_id = Column(String, ForeignKey("old_live_classes.id"))
    title       = Column(String(255))
    description = Column(Text)
    due_date    = Column(DateTime)
    
    live_class  = relationship("OldLiveClass", back_populates="assignments")

# ─────────────────────────────────────────────
# 4. CLASS COMMUNICATION PORTAL
# ─────────────────────────────────────────────
class ClassForum(Base):
    """Class discussion forum"""
    __tablename__ = "class_forums"
    id          = Column(String, primary_key=True, default=gen_uuid)
    school_class_id = Column(String, ForeignKey("school_classes.id"), nullable=True)
    course_id   = Column(String, ForeignKey("courses.id"), nullable=True)
    title       = Column(String(255))
    description = Column(Text)
    created_by  = Column(String, ForeignKey("users.id"))
    created_at  = Column(DateTime, server_default=func.now())
    
    threads     = relationship("ForumThread", back_populates="forum")

class ForumThread(Base):
    """Discussion threads"""
    __tablename__ = "forum_threads"
    id          = Column(String, primary_key=True, default=gen_uuid)
    forum_id    = Column(String, ForeignKey("class_forums.id"))
    author_id   = Column(String, ForeignKey("users.id"))
    title       = Column(String(255))
    content     = Column(Text)
    views       = Column(Integer, default=0)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    forum       = relationship("ClassForum", back_populates="threads")
    replies     = relationship("ForumReply", back_populates="thread")

class ForumReply(Base):
    """Replies to forum threads"""
    __tablename__ = "forum_replies"
    id          = Column(String, primary_key=True, default=gen_uuid)
    thread_id   = Column(String, ForeignKey("forum_threads.id"))
    author_id   = Column(String, ForeignKey("users.id"))
    content     = Column(Text)
    file_url    = Column(String(500), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    
    thread      = relationship("ForumThread", back_populates="replies")

class StudyGroup(Base):
    """Student study groups"""
    __tablename__ = "study_groups"
    id          = Column(String, primary_key=True, default=gen_uuid)
    name        = Column(String(255))
    description = Column(Text)
    creator_id  = Column(String, ForeignKey("users.id"))
    school_class_id = Column(String, ForeignKey("school_classes.id"), nullable=True)
    course_id   = Column(String, ForeignKey("courses.id"), nullable=True)
    max_members = Column(Integer, default=10)
    created_at  = Column(DateTime, server_default=func.now())
    
    members     = relationship("StudyGroupMember", back_populates="study_group")

class StudyGroupMember(Base):
    """Members of study groups"""
    __tablename__ = "study_group_members"
    id          = Column(String, primary_key=True, default=gen_uuid)
    study_group_id = Column(String, ForeignKey("study_groups.id"))
    student_id  = Column(String, ForeignKey("users.id"))
    joined_at   = Column(DateTime, server_default=func.now())
    
    study_group = relationship("StudyGroup", back_populates="members")

# ─────────────────────────────────────────────
# 5. CODING & DEVELOPMENT LAB
# ─────────────────────────────────────────────
class CodeLabProject(Base):
    """Coding projects in the code lab"""
    __tablename__ = "code_lab_projects"
    id          = Column(String, primary_key=True, default=gen_uuid)
    title       = Column(String(255))
    description = Column(Text)
    language    = Column(String(50))  # python/java/javascript/go/rust/cpp/c#
    difficulty  = Column(String(20))  # beginner/intermediate/advanced
    creator_id  = Column(String, ForeignKey("users.id"))
    course_id   = Column(String, ForeignKey("courses.id"), nullable=True)
    starter_code = Column(Text)
    test_cases  = Column(JSON)  # [{input, expected_output}]
    is_public   = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())
    
    submissions = relationship("CodeSubmission", back_populates="project")

class CodeSubmission(Base):
    """Student code submissions"""
    __tablename__ = "code_submissions"
    id          = Column(String, primary_key=True, default=gen_uuid)
    project_id  = Column(String, ForeignKey("code_lab_projects.id"))
    student_id  = Column(String, ForeignKey("users.id"))
    code        = Column(Text)
    language    = Column(String(50))
    status      = Column(String(20))  # compiled/runtime_error/wrong_output/accepted
    test_passed = Column(Integer, default=0)  # num of tests passed
    execution_time = Column(Float)  # seconds
    ai_feedback = Column(Text)
    submitted_at = Column(DateTime, server_default=func.now())
    
    project     = relationship("CodeLabProject", back_populates="submissions")

class CodeExecutionResult(Base):
    """Results of code execution"""
    __tablename__ = "code_execution_results"
    id          = Column(String, primary_key=True, default=gen_uuid)
    submission_id = Column(String, ForeignKey("code_submissions.id"))
    test_case_id = Column(String)
    output      = Column(Text)
    expected_output = Column(Text)
    status      = Column(String(20))  # passed/failed
    error_message = Column(Text, nullable=True)

# ─────────────────────────────────────────────
# 6. PROFESSIONAL COURSES MARKETPLACE
# ─────────────────────────────────────────────
class ProfessionalCourse(Base):
    """Professional/marketplace courses (Coursera/Udemy style)"""
    __tablename__ = "professional_courses"
    id          = Column(String, primary_key=True, default=gen_uuid)
    title       = Column(String(500))
    description = Column(Text)
    category    = Column(String(100))  # AI/ML, Cyber Security, DevOps, Cloud, etc.
    subcategory = Column(String(100))
    instructor_id = Column(String, ForeignKey("users.id"))
    price       = Column(Float, default=0)
    currency    = Column(String(10), default="USD")
    difficulty  = Column(String(20))
    rating      = Column(Float, default=0)
    total_rating_count = Column(Integer, default=0)
    total_students = Column(Integer, default=0)
    total_duration = Column(Integer)  # hours
    thumbnail   = Column(String(500))
    promo_video = Column(String(500))
    is_published = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())
    
    sections    = relationship("CourseSection", back_populates="course")
    enrollments = relationship("ProfessionalEnrollment", back_populates="course")
    reviews     = relationship("CourseReview", back_populates="course")

class CourseSection(Base):
    """Sections/modules in professional courses"""
    __tablename__ = "course_sections"
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("professional_courses.id"))
    title       = Column(String(255))
    description = Column(Text)
    order_index = Column(Integer)
    
    course      = relationship("ProfessionalCourse", back_populates="sections")
    lessons     = relationship("CourseLesson", back_populates="section")

class CourseLesson(Base):
    """Individual lessons in course sections"""
    __tablename__ = "course_lessons"
    id          = Column(String, primary_key=True, default=gen_uuid)
    section_id  = Column(String, ForeignKey("course_sections.id"))
    title       = Column(String(255))
    description = Column(Text)
    video_url   = Column(String(500))
    duration    = Column(Integer)  # seconds
    order_index = Column(Integer)
    resources   = Column(JSON, default=list)  # URLs and files
    
    section     = relationship("CourseSection", back_populates="lessons")

class ProfessionalEnrollment(Base):
    """Student enrollments in professional courses"""
    __tablename__ = "professional_enrollments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    course_id   = Column(String, ForeignKey("professional_courses.id"))
    progress    = Column(Integer, default=0)  # percentage
    completed   = Column(Boolean, default=False)
    certificate_issued = Column(Boolean, default=False)
    enrolled_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    student     = relationship("User")
    course      = relationship("ProfessionalCourse", back_populates="enrollments")

class CourseReview(Base):
    """Reviews for professional courses"""
    __tablename__ = "course_reviews"
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("professional_courses.id"))
    student_id  = Column(String, ForeignKey("users.id"))
    rating      = Column(Integer)  # 1-5
    review_text = Column(Text)
    helpful_count = Column(Integer, default=0)
    created_at  = Column(DateTime, server_default=func.now())
    
    course      = relationship("ProfessionalCourse", back_populates="reviews")

# ─────────────────────────────────────────────
# 7. COMPETITIVE EXAMINATION MODULE
# ─────────────────────────────────────────────
class CompetitiveExam(Base):
    """Competitive exam preparation courses"""
    __tablename__ = "competitive_exams"
    id          = Column(String, primary_key=True, default=gen_uuid)
    exam_name   = Column(String(255))  # UPSC, JEE, NEET, CAT, etc.
    exam_type   = Column(String(50))   # government/engineering/medical/commerce/entrance
    description = Column(Text)
    difficulty  = Column(String(20))
    instructor_id = Column(String, ForeignKey("users.id"))
    created_at  = Column(DateTime, server_default=func.now())
    
    study_materials = relationship("ExamStudyMaterial", back_populates="exam")
    mock_tests  = relationship("MockTest", back_populates="exam")
    enrollments = relationship("ExamEnrollment", back_populates="exam")

class ExamStudyMaterial(Base):
    """Study materials for competitive exams"""
    __tablename__ = "exam_study_materials"
    id          = Column(String, primary_key=True, default=gen_uuid)
    exam_id     = Column(String, ForeignKey("competitive_exams.id"))
    title       = Column(String(255))
    topic       = Column(String(100))
    material_type = Column(String(50))  # notes/video/book/previous_paper
    url         = Column(String(500), nullable=True)
    file_path   = Column(String(500), nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"))
    views       = Column(Integer, default=0)
    created_at  = Column(DateTime, server_default=func.now())
    
    exam        = relationship("CompetitiveExam", back_populates="study_materials")

class MockTest(Base):
    """Mock tests for competitive exams"""
    __tablename__ = "mock_tests"
    id          = Column(String, primary_key=True, default=gen_uuid)
    exam_id     = Column(String, ForeignKey("competitive_exams.id"))
    title       = Column(String(255))
    duration    = Column(Integer)  # minutes
    total_questions = Column(Integer)
    total_marks = Column(Integer)
    negative_marking = Column(Float, default=0)
    description = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())
    
    exam        = relationship("CompetitiveExam", back_populates="mock_tests")
    questions   = relationship("MockTestQuestion", back_populates="mock_test")
    attempts    = relationship("MockTestAttempt", back_populates="mock_test")

class MockTestQuestion(Base):
    """Questions in mock tests"""
    __tablename__ = "mock_test_questions"
    id          = Column(String, primary_key=True, default=gen_uuid)
    mock_test_id = Column(String, ForeignKey("mock_tests.id"))
    question    = Column(Text)
    options     = Column(JSON)  # ["A", "B", "C", "D"]
    correct_answer = Column(String)
    explanation = Column(Text)
    marks       = Column(Integer)
    order_index = Column(Integer)
    
    mock_test   = relationship("MockTest", back_populates="questions")

class MockTestAttempt(Base):
    """Student attempts at mock tests"""
    __tablename__ = "mock_test_attempts"
    id          = Column(String, primary_key=True, default=gen_uuid)
    mock_test_id = Column(String, ForeignKey("mock_tests.id"))
    student_id  = Column(String, ForeignKey("users.id"))
    score       = Column(Float)
    percentage  = Column(Float)
    time_taken  = Column(Integer)  # seconds
    ai_analysis = Column(Text)  # AI-generated performance analysis
    attempted_at = Column(DateTime, server_default=func.now())
    
    mock_test   = relationship("MockTest", back_populates="attempts")

class ExamEnrollment(Base):
    """Student enrollment in exam prep courses"""
    __tablename__ = "exam_enrollments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    exam_id     = Column(String, ForeignKey("competitive_exams.id"))
    enrolled_at = Column(DateTime, server_default=func.now())
    
    student     = relationship("User")
    exam        = relationship("CompetitiveExam", back_populates="enrollments")

# ─────────────────────────────────────────────
# 8. AI INTERVIEW PREPARATION
# ─────────────────────────────────────────────
class Resume(Base):
    """Student resumes"""
    __tablename__ = "resumes"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    title       = Column(String(255))
    file_url    = Column(String(500))
    parsed_data = Column(JSON)  # {skills, experience, education, etc.}
    ats_score   = Column(Float, nullable=True)
    gap_analysis = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    is_current  = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

class JobDescription(Base):
    """Job descriptions for interview prep"""
    __tablename__ = "job_descriptions"
    id          = Column(String, primary_key=True, default=gen_uuid)
    title       = Column(String(255))
    company     = Column(String(255))
    description = Column(Text)
    required_skills = Column(JSON)
    experience_needed = Column(String(50))
    parsed_data = Column(JSON)
    created_at  = Column(DateTime, server_default=func.now())

class InterviewPrep(Base):
    """AI interview preparation sessions"""
    __tablename__ = "interview_preps"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    resume_id   = Column(String, ForeignKey("resumes.id"), nullable=True)
    job_desc_id = Column(String, ForeignKey("job_descriptions.id"), nullable=True)
    interview_type = Column(String(50))  # technical/behavioral/hr/system_design
    questions   = Column(JSON)  # AI-generated questions
    created_at  = Column(DateTime, server_default=func.now())

class VideoInterview(Base):
    """AI video interview simulations"""
    __tablename__ = "video_interviews"
    id          = Column(String, primary_key=True, default=gen_uuid)
    interview_prep_id = Column(String, ForeignKey("interview_preps.id"))
    video_url   = Column(String(500))
    transcript  = Column(Text)
    eye_contact_score = Column(Float)
    confidence_score = Column(Float)
    communication_score = Column(Float)
    technical_score = Column(Float)
    overall_score = Column(Float)
    feedback    = Column(Text)  # AI feedback
    improvement_areas = Column(JSON)
    created_at  = Column(DateTime, server_default=func.now())

class InterviewReport(Base):
    """Comprehensive interview performance reports"""
    __tablename__ = "interview_reports"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    video_interview_id = Column(String, ForeignKey("video_interviews.id"))
    ats_score   = Column(Float)
    resume_gap_score = Column(Float)
    skill_gap_score = Column(Float)
    interview_readiness = Column(Float)
    recommendations = Column(JSON)
    created_at  = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# 9. PLACEMENT & CAREER PORTAL
# ─────────────────────────────────────────────
class JobListing(Base):
    """Job listings on the platform"""
    __tablename__ = "job_listings"
    id          = Column(String, primary_key=True, default=gen_uuid)
    title       = Column(String(255))
    company     = Column(String(255))
    description = Column(Text)
    salary_min  = Column(Float, nullable=True)
    salary_max  = Column(Float, nullable=True)
    currency    = Column(String(10), default="USD")
    location    = Column(String(255))
    job_type    = Column(String(50))  # full_time/part_time/intern
    experience_needed = Column(String(50))
    required_skills = Column(JSON)
    recruiter_id = Column(String, ForeignKey("users.id"))
    posted_at   = Column(DateTime, server_default=func.now())
    deadline    = Column(DateTime)
    is_active   = Column(Boolean, default=True)
    
    applications = relationship("OldJobApplication", back_populates="job")

class InternshipListing(Base):
    """Internship listings"""
    __tablename__ = "internship_listings"
    id          = Column(String, primary_key=True, default=gen_uuid)
    title       = Column(String(255))
    company     = Column(String(255))
    description = Column(Text)
    stipend     = Column(Float, nullable=True)
    duration    = Column(String(50))  # e.g., "3 months"
    location    = Column(String(255))
    required_skills = Column(JSON)
    recruiter_id = Column(String, ForeignKey("users.id"))
    posted_at   = Column(DateTime, server_default=func.now())
    deadline    = Column(DateTime)
    is_active   = Column(Boolean, default=True)

class OldJobApplication(Base):
    """Student job applications"""
    __tablename__ = "old_job_applications"
    id          = Column(String, primary_key=True, default=gen_uuid)
    job_id      = Column(String, ForeignKey("job_listings.id"))
    student_id  = Column(String, ForeignKey("users.id"))
    resume_id   = Column(String, ForeignKey("resumes.id"))
    cover_letter = Column(Text, nullable=True)
    status      = Column(String(50))  # applied/screening/interview/offer/rejected
    applied_at  = Column(DateTime, server_default=func.now())
    
    job         = relationship("JobListing", back_populates="applications")

class Portfolio(Base):
    """Student portfolios"""
    __tablename__ = "portfolios"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    title       = Column(String(255))
    bio         = Column(Text)
    website_url = Column(String(500), nullable=True)
    github_url  = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    
    projects    = relationship("PortfolioProject", back_populates="portfolio")

class PortfolioProject(Base):
    """Projects in portfolio"""
    __tablename__ = "portfolio_projects"
    id          = Column(String, primary_key=True, default=gen_uuid)
    portfolio_id = Column(String, ForeignKey("portfolios.id"))
    title       = Column(String(255))
    description = Column(Text)
    technologies = Column(JSON)
    github_link = Column(String(500), nullable=True)
    live_link   = Column(String(500), nullable=True)
    image_url   = Column(String(500), nullable=True)
    
    portfolio   = relationship("Portfolio", back_populates="projects")

# ─────────────────────────────────────────────
# 10. INSTITUTION/ORGANIZATION MANAGEMENT
# ─────────────────────────────────────────────
class Institution(Base):
    """Schools, colleges, training centers"""
    __tablename__ = "institutions"
    id          = Column(String, primary_key=True, default=gen_uuid)
    name        = Column(String(255))
    institution_type = Column(String(50))  # school/college/university/training_center
    address     = Column(Text)
    city        = Column(String(100))
    state       = Column(String(100))
    country     = Column(String(100))
    phone       = Column(String(20))
    email       = Column(String(255))
    website     = Column(String(500))
    admin_id    = Column(String, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# 11. AI TUTOR & RAG SYSTEM
# ─────────────────────────────────────────────
class OldAITutorSession(Base):
    """AI tutor chat sessions"""
    __tablename__ = "old_ai_tutor_sessions"
    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id"))
    subject_id  = Column(String, nullable=True)  # school_subject or college_subject
    topic       = Column(String(255))
    messages    = Column(JSON)  # [{role, content, timestamp}]
    language    = Column(String(50), default="English")
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user        = relationship("User")

class OldRAGDocument(Base):
    """Documents indexed in RAG system"""
    __tablename__ = "old_rag_documents"
    id          = Column(String, primary_key=True, default=gen_uuid)
    document_type = Column(String(50))  # lecture_note/book/research_paper
    title       = Column(String(255))
    content     = Column(Text)
    source_url  = Column(String(500), nullable=True)
    embeddings  = Column(JSON)  # Vector embeddings (optional, can be in vector DB)
    chroma_doc_ids = Column(JSON, default=list)  # ChromaDB document IDs
    created_at  = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# 12. GAMIFICATION & REWARDS
# ─────────────────────────────────────────────
class OldUserPoints(Base):
    """Gamification points system"""
    __tablename__ = "old_user_points"
    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id"), unique=True)
    total_points = Column(Integer, default=0)
    total_badges = Column(Integer, default=0)
    total_streaks = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user        = relationship("User")

class OldBadge(Base):
    """Achievement badges"""
    __tablename__ = "old_badges"
    id          = Column(String, primary_key=True, default=gen_uuid)
    name        = Column(String(100))
    description = Column(Text)
    icon_url    = Column(String(500))
    criteria    = Column(JSON)  # {type, count}
    created_at  = Column(DateTime, server_default=func.now())

class OldUserBadge(Base):
    """Badges earned by users"""
    __tablename__ = "old_user_badges"
    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id"))
    badge_id    = Column(String, ForeignKey("badges.id"))
    earned_at   = Column(DateTime, server_default=func.now())

class Leaderboard(Base):
    """Leaderboard rankings"""
    __tablename__ = "leaderboards"
    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id"))
    category    = Column(String(100))  # global/course/subject/weekly/monthly
    rank        = Column(Integer)
    score       = Column(Integer)
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

# ─────────────────────────────────────────────
# 13. ANALYTICS & PROGRESS TRACKING
# ─────────────────────────────────────────────
class StudentAnalytics(Base):
    """Detailed student learning analytics"""
    __tablename__ = "student_analytics"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"), unique=True)
    total_learning_hours = Column(Float, default=0)
    total_courses_enrolled = Column(Integer, default=0)
    total_courses_completed = Column(Integer, default=0)
    average_score = Column(Float, default=0)
    last_activity = Column(DateTime, nullable=True)
    skill_progress = Column(JSON)  # {skill: progress_percentage}
    learning_pace = Column(String(50))  # slow/normal/fast
    learning_style = Column(String(100))  # visual/auditory/kinesthetic
    weak_areas   = Column(JSON, default=list)
    strong_areas = Column(JSON, default=list)
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TeacherAnalytics(Base):
    """Teacher performance analytics"""
    __tablename__ = "teacher_analytics"
    id          = Column(String, primary_key=True, default=gen_uuid)
    teacher_id  = Column(String, ForeignKey("users.id"), unique=True)
    total_courses = Column(Integer, default=0)
    total_students = Column(Integer, default=0)
    average_rating = Column(Float, default=0)
    total_reviews = Column(Integer, default=0)
    engagement_score = Column(Float, default=0)
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

# ─────────────────────────────────────────────
# ADDITIONAL SUPPORTING MODELS
# ─────────────────────────────────────────────
class OldReview(Base):
    """Generic reviews (kept for backward compatibility)"""
    __tablename__ = "old_reviews"
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("courses.id"))
    user_id     = Column(String, ForeignKey("users.id"))
    rating      = Column(Integer, default=5)
    text        = Column(Text)
    helpful     = Column(Integer, default=0)
    created_at  = Column(DateTime, server_default=func.now())
    
    course      = relationship("Course")

class OldCertificate(Base):
    """Certificates issued to students"""
    __tablename__ = "old_certificates"
    id          = Column(String, primary_key=True, default=gen_uuid)
    student_id  = Column(String, ForeignKey("users.id"))
    course_id   = Column(String, ForeignKey("courses.id"), nullable=True)
    exam_id     = Column(String, ForeignKey("competitive_exams.id"), nullable=True)
    certificate_type = Column(String(50))  # completion/achievement/exam_pass
    issued_date = Column(DateTime, server_default=func.now())
    certificate_url = Column(String(500))
    verification_code = Column(String(50), unique=True)

class OldPayment(Base):
    """Payment transactions"""
    __tablename__ = "old_payments"
    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id"))
    amount      = Column(Float)
    currency    = Column(String(10))
    payment_method = Column(String(50))  # stripe/razorpay/paypal
    status      = Column(String(20))  # pending/completed/failed
    stripe_payment_id = Column(String(255), nullable=True)
    description = Column(Text)
    created_at  = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# CERTIFICATE
# ─────────────────────────────────────────────
class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = {'extend_existing': True}
    id              = Column(String, primary_key=True, default=gen_uuid)
    student_id      = Column(String, ForeignKey("users.id"))
    course_id       = Column(String, ForeignKey("courses.id"))
    certificate_url = Column(String(500))
    verify_code     = Column(String(50), unique=True)
    issued_at       = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# REVIEW
# ─────────────────────────────────────────────
class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = {'extend_existing': True}
    id         = Column(String, primary_key=True, default=gen_uuid)
    course_id  = Column(String, ForeignKey("courses.id"))
    student_id = Column(String, ForeignKey("users.id"))
    rating     = Column(Integer)
    comment    = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    course     = relationship("Course", back_populates="reviews")

# ─────────────────────────────────────────────
# GAMIFICATION
# ─────────────────────────────────────────────
class UserPoints(Base):
    __tablename__ = "user_points"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    user_id       = Column(String, ForeignKey("users.id"), unique=True)
    xp            = Column(Integer, default=0)
    level         = Column(Integer, default=1)
    streak_days   = Column(Integer, default=0)
    longest_streak= Column(Integer, default=0)
    last_activity = Column(String, nullable=True)
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user          = relationship("User", back_populates="points")

class Badge(Base):
    __tablename__ = "badges"
    __table_args__ = {'extend_existing': True}
    id              = Column(String, primary_key=True, default=gen_uuid)
    name            = Column(String(100))
    description     = Column(Text)
    icon            = Column(String(10))
    condition_type  = Column(String(50))   # courses_completed/xp_earned/streak/quiz_perfect
    condition_value = Column(Integer)
    color           = Column(String(20), default="#6366f1")

class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = {'extend_existing': True}
    id        = Column(String, primary_key=True, default=gen_uuid)
    user_id   = Column(String, ForeignKey("users.id"))
    badge_id  = Column(String, ForeignKey("badges.id"))
    earned_at = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# STUDY PLAN
# ─────────────────────────────────────────────
class StudyPlan(Base):
    __tablename__ = "study_plans"
    id           = Column(String, primary_key=True, default=gen_uuid)
    student_id   = Column(String, ForeignKey("users.id"))
    title        = Column(String(255))
    goal         = Column(Text)
    target_date  = Column(String)
    weekly_hours = Column(Integer, default=5)
    schedule     = Column(JSON)          # [{day, topic, duration, course_id}]
    milestones   = Column(JSON)          # [{title, due, completed}]
    ai_generated = Column(Boolean, default=False)
    created_at   = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# AI TUTOR SESSION
# ─────────────────────────────────────────────
class AITutorSession(Base):
    __tablename__ = "ai_tutor_sessions"
    __table_args__ = {'extend_existing': True}
    id         = Column(String, primary_key=True, default=gen_uuid)
    user_id    = Column(String, ForeignKey("users.id"))
    course_id  = Column(String, ForeignKey("courses.id"), nullable=True)
    title      = Column(String(255))
    messages   = Column(JSON, default=list)   # [{role, content, timestamp}]
    context    = Column(Text)                 # RAG context summary
    topic      = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user       = relationship("User", back_populates="ai_sessions")

# ─────────────────────────────────────────────
# LIVE CLASS
# ─────────────────────────────────────────────
class LiveClass(Base):
    __tablename__ = "live_classes"
    __table_args__ = {'extend_existing': True}
    id               = Column(String, primary_key=True, default=gen_uuid)
    course_id        = Column(String, ForeignKey("courses.id"))
    faculty_id       = Column(String, ForeignKey("users.id"))
    title            = Column(String(500))
    description      = Column(Text)
    scheduled_at     = Column(DateTime)
    duration_minutes = Column(Integer, default=60)
    platform         = Column(String(20), default="zoom")  # zoom/meet/teams/custom
    meeting_url      = Column(String(500))
    meeting_id       = Column(String(100))
    meeting_password = Column(String(100))
    status           = Column(String(20), default="scheduled")
    recording_url    = Column(String(500))
    created_at       = Column(DateTime, server_default=func.now())

    course           = relationship("Course", back_populates="live_classes")

# ─────────────────────────────────────────────
# CAREER
# ─────────────────────────────────────────────
class Internship(Base):
    __tablename__ = "internships"
    id           = Column(String, primary_key=True, default=gen_uuid)
    title        = Column(String(500))
    company      = Column(String(255))
    description  = Column(Text)
    location     = Column(String(255))
    type         = Column(String(20))    # internship/job/freelance
    stipend      = Column(String(100))
    skills       = Column(JSON, default=list)
    apply_url    = Column(String(500))
    deadline     = Column(String)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────
class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {'extend_existing': True}
    id              = Column(String, primary_key=True, default=gen_uuid)
    student_id      = Column(String, ForeignKey("users.id"))
    course_id       = Column(String, ForeignKey("courses.id"))
    stripe_id       = Column(String(255))
    amount          = Column(Float)
    currency        = Column(String(10), default="usd")
    status          = Column(String(20))   # succeeded/failed/pending
    created_at      = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# RAG DOCUMENT INDEX
# ─────────────────────────────────────────────
class RAGDocument(Base):
    __tablename__ = "rag_documents"
    __table_args__ = {'extend_existing': True}
    id          = Column(String, primary_key=True, default=gen_uuid)
    course_id   = Column(String, ForeignKey("courses.id"))
    lecture_id  = Column(String, ForeignKey("lectures.id"), nullable=True)
    source_type = Column(String(20))     # pdf/video_transcript/web
    source_url  = Column(String(500))
    content     = Column(Text)
    chunk_count = Column(Integer, default=0)
    is_indexed  = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# AI MOCK INTERVIEW SESSIONS
# ─────────────────────────────────────────────
class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id                = Column(String, primary_key=True, default=gen_uuid)
    user_id           = Column(String, ForeignKey("users.id"))
    resume_text       = Column(Text, nullable=True)
    job_description   = Column(Text, nullable=True)
    questions         = Column(JSON, default=list)      # [{"id", "type", "question", "options", "answer", "explanation"}]
    chat_history      = Column(JSON, default=list)      # [{role: "bot"|"user", content: "...", voice_data: "..."}]
    ats_score         = Column(Integer, default=0)
    gap_analysis      = Column(JSON, default=dict)      # {"skills_missing": [], "improvements": []}
    readiness_score   = Column(Integer, default=0)
    eye_contact_score = Column(Integer, default=0)
    confidence_score  = Column(Integer, default=0)
    eval_report       = Column(Text, nullable=True)     # Detailed AI Evaluation report
    created_at        = Column(DateTime, server_default=func.now())
    updated_at        = Column(DateTime, server_default=func.now(), onupdate=func.now())

# ─────────────────────────────────────────────
# CODE LAB SNIPPETS
# ─────────────────────────────────────────────
class CodeSnippet(Base):
    __tablename__ = "code_snippets"
    id          = Column(String, primary_key=True, default=gen_uuid)
    user_id     = Column(String, ForeignKey("users.id"))
    title       = Column(String(255), default="Untitled Snippet")
    language    = Column(String(50), default="python")
    code        = Column(Text, nullable=False)
    ai_review   = Column(Text, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

# ─────────────────────────────────────────────
# JOB APPLICATIONS
# ─────────────────────────────────────────────
class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    student_id    = Column(String, ForeignKey("users.id"))
    internship_id = Column(String, ForeignKey("internships.id"))
    status        = Column(String(50), default="Applied") # Applied, Reviewing, Shortlisted, Rejected
    resume_url    = Column(String(500), nullable=True)
    cover_letter  = Column(Text, nullable=True)
    applied_at    = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# TRAINING BATCHES
# ─────────────────────────────────────────────
class TrainingBatch(Base):
    __tablename__ = "training_batches"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    name          = Column(String(255), nullable=False)
    course_id     = Column(String, ForeignKey("courses.id"), nullable=True)
    faculty_id    = Column(String, ForeignKey("users.id"))
    start_date    = Column(DateTime)
    end_date      = Column(DateTime)
    status        = Column(String(50), default="Upcoming") # Upcoming, Ongoing, Completed
    max_capacity  = Column(Integer, default=50)
    created_at    = Column(DateTime, server_default=func.now())

class BatchStudent(Base):
    __tablename__ = "batch_students"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    batch_id      = Column(String, ForeignKey("training_batches.id"))
    student_id    = Column(String, ForeignKey("users.id"))
    joined_at     = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# COMMUNICATION / GROUPS
# ─────────────────────────────────────────────
class GroupChat(Base):
    __tablename__ = "group_chats"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    name          = Column(String(255), nullable=False)
    batch_id      = Column(String, ForeignKey("training_batches.id"), nullable=True)
    course_id     = Column(String, ForeignKey("courses.id"), nullable=True)
    created_by    = Column(String, ForeignKey("users.id"))
    created_at    = Column(DateTime, server_default=func.now())

class GroupMessage(Base):
    __tablename__ = "group_messages"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    group_id      = Column(String, ForeignKey("group_chats.id"))
    sender_id     = Column(String, ForeignKey("users.id"))
    content       = Column(Text, nullable=False)
    attachment    = Column(String(500), nullable=True)
    created_at    = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# RESOURCE HUB
# ─────────────────────────────────────────────
class ResourceHub(Base):
    __tablename__ = "resource_hub"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    title         = Column(String(500), nullable=False)
    domain        = Column(String(100)) # e.g. C++, Java, Cloud, Law
    url           = Column(String(500), nullable=True)
    resource_type = Column(String(50))  # article, video, leetcode, github
    description   = Column(Text)
    created_by    = Column(String, ForeignKey("users.id"), nullable=True)
    created_at    = Column(DateTime, server_default=func.now())

# ─────────────────────────────────────────────
# PROJECT CATALOG
# ─────────────────────────────────────────────
class ProjectCatalog(Base):
    __tablename__ = "project_catalog"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    title         = Column(String(500), nullable=False)
    domain        = Column(String(100)) # Web Dev, AI, Security
    level         = Column(String(50))  # Beginner, Intermediate, Advanced
    description   = Column(Text)
    github_url    = Column(String(500), nullable=True)
    live_url      = Column(String(500), nullable=True)
    tutorial_url  = Column(String(500), nullable=True)
    tags          = Column(JSON, default=list)
    created_at    = Column(DateTime, server_default=func.now())

class ProjectPlaylist(Base):
    __tablename__ = "project_playlists"
    __table_args__ = {'extend_existing': True}
    id            = Column(String, primary_key=True, default=gen_uuid)
    project_id    = Column(String, ForeignKey("project_catalog.id"))
    title         = Column(String(500))
    video_url     = Column(String(500))
    order_index   = Column(Integer, default=0)
    created_at    = Column(DateTime, server_default=func.now())
