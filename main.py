from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn, os

from database import engine, Base
from routers import auth, users, courses, lectures, quizzes, assignments
from routers import chat, ai, certificates, analytics, gamification
from routers import notifications, payments, career, study_plan, resume, admin

# Create tables
Base.metadata.create_all(bind=engine)

# Create upload dirs
os.makedirs("static/uploads/avatars", exist_ok=True)
os.makedirs("static/uploads/thumbnails", exist_ok=True)
os.makedirs("static/uploads/videos", exist_ok=True)
os.makedirs("static/uploads/certificates", exist_ok=True)
os.makedirs("static/uploads/files", exist_ok=True)

app = FastAPI(title="EduAI Platform", version="2.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API Routers
app.include_router(auth.router,           prefix="/api/auth",          tags=["Auth"])
app.include_router(users.router,          prefix="/api/users",         tags=["Users"])
app.include_router(courses.router,        prefix="/api/courses",       tags=["Courses"])
app.include_router(lectures.router,       prefix="/api/lectures",      tags=["Lectures"])
app.include_router(quizzes.router,        prefix="/api/quizzes",       tags=["Quizzes"])
app.include_router(assignments.router,    prefix="/api/assignments",   tags=["Assignments"])
app.include_router(chat.router,           prefix="/api/chat",          tags=["Chat"])
app.include_router(ai.router,             prefix="/api/ai",            tags=["AI"])
app.include_router(certificates.router,   prefix="/api/certificates",  tags=["Certificates"])
app.include_router(analytics.router,      prefix="/api/analytics",     tags=["Analytics"])
app.include_router(gamification.router,   prefix="/api/gamification",  tags=["Gamification"])
app.include_router(notifications.router,  prefix="/api/notifications", tags=["Notifications"])
app.include_router(payments.router,       prefix="/api/payments",      tags=["Payments"])
app.include_router(career.router,         prefix="/api/career",        tags=["Career"])
app.include_router(study_plan.router,     prefix="/api/study-plan",    tags=["Study Plan"])
app.include_router(resume.router,         prefix="/api/resume",        tags=["Resume"])
app.include_router(admin.router,          prefix="/api/admin",         tags=["Admin"])

# Serve HTML pages
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/{page}", response_class=HTMLResponse)
async def pages(request: Request, page: str):
    valid = ["login","register","dashboard","courses","ai-guide","chat",
             "leaderboard","certificates","analytics","career","study-plan",
             "admin","faculty","profile","quiz","live-class"]
    if page in valid:
        return templates.TemplateResponse(f"{page}.html", {"request": request})
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "app": "EduAI Platform"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
