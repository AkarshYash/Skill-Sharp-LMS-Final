from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn, os

from database import engine, Base
from routers import (
    auth, users, courses, lectures, quizzes, assignments,
    chat, ai, certificates, analytics, gamification,
    notifications, payments, career, study_plan, resume,
    admin, live_class, code_lab, interview,
    school_education, college_education, competitive_exams,
    interview_prep, career_portal, professional_courses,
    groups, resources, projects, jobseekers
)

# Create all DB tables
Base.metadata.create_all(bind=engine)

# Create upload directories
for d in [
    "static/uploads/avatars",
    "static/uploads/thumbnails",
    "static/uploads/videos",
    "static/uploads/notes",
    "static/uploads/certificates",
    "static/uploads/assignments",
    "static/uploads/files",
    "chroma_db",
    "templates",
]:
    os.makedirs(d, exist_ok=True)

app = FastAPI(
    title       = "Skills Sharp 365 Innovation",
    description = "AI-powered unified learning ecosystem: Recorded Courses, Live Training, School Education, College Programs, Competitive Exams, Interview Prep, Career Portal, Coding Lab, Professional Courses, and AI Mentorship",
    version     = "4.0.0",
    docs_url    = "/api/docs",
    redoc_url   = "/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─── API Routers ────────────────────────────────────────
app.include_router(auth.router,             prefix="/api/auth",              tags=["Auth"])
app.include_router(users.router,            prefix="/api/users",             tags=["Users"])
app.include_router(courses.router,          prefix="/api/courses",           tags=["Courses"])
app.include_router(lectures.router,         prefix="/api/lectures",          tags=["Lectures"])
app.include_router(quizzes.router,          prefix="/api/quizzes",           tags=["Quizzes"])
app.include_router(assignments.router,      prefix="/api/assignments",       tags=["Assignments"])
app.include_router(chat.router,             prefix="/api/chat",              tags=["Chat"])
app.include_router(ai.router,               prefix="/api/ai",                tags=["AI / LangChain"])
app.include_router(certificates.router,     prefix="/api/certificates",      tags=["Certificates"])
app.include_router(analytics.router,        prefix="/api/analytics",         tags=["Analytics"])
app.include_router(gamification.router,     prefix="/api/gamification",      tags=["Gamification"])
app.include_router(notifications.router,    prefix="/api/notifications",     tags=["Notifications"])
app.include_router(payments.router,         prefix="/api/payments",          tags=["Payments"])
app.include_router(career.router,           prefix="/api/career",            tags=["Career"])
app.include_router(study_plan.router,       prefix="/api/study-plan",        tags=["Study Plan"])
app.include_router(resume.router,           prefix="/api/resume",            tags=["Resume"])
app.include_router(admin.router,            prefix="/api/admin",             tags=["Admin"])
app.include_router(live_class.router,       prefix="/api/live-class",        tags=["Live Class"])
app.include_router(code_lab.router,         prefix="/api/code-lab",          tags=["Coding Lab"])
app.include_router(interview.router,        prefix="/api/interview",         tags=["AI Interview"])

# ─── Skill Sharp 365 NEW MODULES ────────────────────────
app.include_router(school_education.router,     prefix="/api/school",            tags=["School Education"])
app.include_router(college_education.router,    prefix="/api/college",           tags=["College Education"])
# NOTE: live_class.router is already mounted above at /api/live-class — not duplicated
app.include_router(competitive_exams.router,    prefix="/api/exams",             tags=["Competitive Exams"])
app.include_router(interview_prep.router,       prefix="/api/interview-prep",    tags=["Interview Prep"])
app.include_router(career_portal.router,        prefix="/api/careers",           tags=["Career Portal"])
app.include_router(professional_courses.router, prefix="/api/pro-courses",       tags=["Professional Courses"])
app.include_router(groups.router,               prefix="/api/groups",            tags=["Groups & Chat"])
app.include_router(resources.router,            prefix="/api/resources",         tags=["Resource Hub"])
app.include_router(projects.router,             prefix="/api/projects",          tags=["Project Catalog"])
app.include_router(jobseekers.router,           prefix="/api/jobseekers",        tags=["Jobseekers"])

# ─── Health & Info ──────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":  "ok",
        "app":     "Skills Sharp 365 Innovation",
        "version": "4.0.0",
        "features": {
            "langchain":   True,
            "rag":         True,
            "gemini":      bool(__import__("config").settings.GEMINI_API_KEY),
            "openai":      bool(__import__("config").settings.OPENAI_API_KEY),
            "stripe":      bool(__import__("config").settings.STRIPE_SECRET_KEY),
        }
    }

# ─── Serve HTML Pages ───────────────────────────────────
VALID_PAGES = [
    "login", "register", "dashboard", "faculty", "admin",
    "courses", "ai-guide", "live-class", "chat", "certificates",
    "leaderboard", "career", "study-plan", "analytics", "profile",
    "quiz", "assignments", "notifications", "settings"
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/verify/{code}", response_class=HTMLResponse)
async def verify_page(request: Request, code: str):
    return templates.TemplateResponse("verify.html", {"request": request, "code": code})

@app.get("/{page}", response_class=HTMLResponse)
async def pages(request: Request, page: str):
    if page in VALID_PAGES:
        try:
            return templates.TemplateResponse(f"{page}.html", {"request": request})
        except Exception:
            return templates.TemplateResponse("index.html", {"request": request})
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
