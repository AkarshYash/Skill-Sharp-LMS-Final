<div align="center">

<img src="https://img.shields.io/badge/Skills_Sharp_365-AI_Powered_LMS-6c63ff?style=for-the-badge&logo=graduation-cap&logoColor=white"/>

# 🎓 Skills Sharp 365 Innovation
### India's #1 AI-Powered Unified Learning Ecosystem

[![Live Demo](https://img.shields.io/badge/🚀_LIVE_DEMO-skill--sharp--lms.onrender.com-00d4aa?style=for-the-badge)](https://skill-sharp-lms.onrender.com)
[![API Docs](https://img.shields.io/badge/📚_API_DOCS-Swagger_UI-6c63ff?style=for-the-badge)](https://skill-sharp-lms.onrender.com/api/docs)
[![GitHub](https://img.shields.io/badge/GitHub-AkarshYash-181717?style=for-the-badge&logo=github)](https://github.com/AkarshYash/Skill-Sharp-LMS-Final)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-RAG_Pipeline-1C3C3C?style=flat-square&logo=chainlink)](https://langchain.com)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-AI_Engine-4285F4?style=flat-square&logo=google)](https://aistudio.google.com)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite)](https://sqlite.org)
[![Render](https://img.shields.io/badge/Deployed_on-Render.com-46E3B7?style=flat-square&logo=render)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

> **From Class 1 to Professional Certifications** — Live classes, recorded courses, AI tutor, coding labs, mock interviews & career guidance, all in one unified platform.

</div>

---

## 📑 Table of Contents

- [🌟 Platform Overview](#-platform-overview)
- [🏗️ Full System Architecture](#️-full-system-architecture)
- [🧩 Tech Stack Breakdown](#-tech-stack-breakdown)
- [🔗 Component Connection Map](#-component-connection-map)
- [✨ Feature Modules](#-feature-modules)
- [🚀 Quick Start](#-quick-start)
- [🔑 Test Credentials](#-test-credentials)
- [📡 API Reference](#-api-reference)
- [🗂️ Project Structure](#️-project-structure)
- [🌐 Deployment Guide](#-deployment-guide)
- [🤝 Contributing](#-contributing)

---

## 🌟 Platform Overview

Skills Sharp 365 is a **full-stack, AI-integrated Learning Management System (LMS)** built with FastAPI on the backend and vanilla HTML/CSS/JS on the frontend, served as a unified monolith. It targets **five distinct learner segments** — school students, college students, competitive exam aspirants, professional learners, and job seekers — all in a single platform.

| Metric | Value |
|--------|-------|
| 🏛️ Architecture | Monolith FastAPI + Jinja2 Templates |
| 🔌 API Endpoints | 80+ REST endpoints across 30 routers |
| 📦 Python Packages | 25+ carefully selected dependencies |
| 🎯 User Roles | Student · Faculty · Admin |
| 🤖 AI Models | Google Gemini 1.5 Flash / OpenAI GPT-3.5 |
| 🗄️ Database | SQLAlchemy ORM + SQLite (PostgreSQL ready) |
| 📡 Realtime | WebSockets via FastAPI |
| 🔐 Auth | JWT Bearer + 2FA (TOTP/QR) |

---

## 🏗️ Full System Architecture

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                         SKILLS SHARP 365 — SYSTEM ARCHITECTURE                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              👤 CLIENT LAYER (Browser)                               │
│                                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  index.html  │  │  login.html  │  │dashboard.html│  │  admin / faculty / others │ │
│  │  (Landing)   │  │  (Auth)      │  │  (Student)   │  │     (Role-Based Pages)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘ │
│         │                 │                  │                        │               │
│         └─────────────────┴──────────────────┴────────────────────────┘               │
│                                      │                                               │
│                        Vanilla JS fetch() API calls                                  │
│                        JWT stored in localStorage                                    │
└──────────────────────────────────────┬──────────────────────────────────────────────┘
                                       │ HTTPS Requests
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            🌐 WEB SERVER LAYER                                       │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                     Uvicorn ASGI Server (port $PORT)                             │ │
│  │              uvicorn main:app --host 0.0.0.0 --port $PORT                       │ │
│  └─────────────────────────────┬───────────────────────────────────────────────────┘ │
│                                 │                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         FastAPI Application (main.py)                            │ │
│  │                                                                                  │ │
│  │  ┌──────────────────────┐     ┌─────────────────────┐     ┌───────────────────┐ │ │
│  │  │   CORS Middleware     │────▶│  JWT Auth Middleware │────▶│  Rate Limiter     │ │ │
│  │  │  (allow_origins=*)   │     │  (HTTPBearer)        │     │  (SlowAPI)        │ │ │
│  │  └──────────────────────┘     └─────────────────────┘     └───────────────────┘ │ │
│  │                                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                         Static File Mount                                │   │ │
│  │  │            /static  ──▶  StaticFiles(directory="static")                 │   │ │
│  │  └──────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                       Jinja2 Template Engine                              │   │ │
│  │  │       GET /  GET /login  GET /dashboard  GET /admin  etc.                │   │ │
│  │  └──────────────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                   ▼
┌────────────────────────┐  ┌──────────────────┐  ┌───────────────────────────────────┐
│   📡 API ROUTER LAYER  │  │  🔐 AUTH LAYER   │  │        🤖 AI SERVICE LAYER         │
│                        │  │                  │  │                                    │
│  /api/auth      ──┐    │  │  auth_utils.py   │  │  services/ai_service.py            │
│  /api/users     ──┤    │  │  ┌────────────┐  │  │  ┌───────────────────────────────┐ │
│  /api/courses   ──┤    │  │  │ JWT Encode │  │  │  │  get_llm()                    │ │
│  /api/lectures  ──┤    │  │  │ JWT Decode │  │  │  │  ├── ChatGoogleGenerativeAI   │ │
│  /api/quizzes   ──┤    │  │  │ BCrypt Hash│  │  │  │  │   (Gemini 1.5 Flash)       │ │
│  /api/ai        ──┤    │  │  │ 2FA TOTP  │  │  │  │  └── ChatOpenAI (fallback)    │ │
│  /api/live-class──┤    │  │  └────────────┘  │  │  │                               │ │
│  /api/analytics ──┤    │  │                  │  │  │  ai_tutor_chat()              │ │
│  /api/payments  ──┤    │  │  require_role()  │  │  │  generate_quiz_questions()    │ │
│  /api/career    ──┤    │  │  get_current_    │  │  │  generate_study_plan()        │ │
│  /api/interview ──┤    │  │  user()          │  │  │  generate_resume()            │ │
│  /api/school    ──┤    │  │                  │  │  │  get_career_recommendations() │ │
│  /api/college   ──┤    │  └──────────────────┘  │  │                               │ │
│  /api/exams     ──┤    │                         │  │  ── fallback mock responses   │ │
│  /api/projects  ──┤    │                         │  │     when no API key set       │ │
│  /api/resources ──┤    │                         │  └───────────────────────────────┘ │
│  ... 30 total   ──┘    │                         │                                    │
└────────────────────────┘                         │  services/rag_service.py           │
                                                   │  ┌───────────────────────────────┐ │
                                                   │  │  index_document()             │ │
                                                   │  │  search_course_context()      │ │
                                                   │  │  ├── ChromaDB (if available)  │ │
                                                   │  │  └── JSON TF-IDF (fallback)   │ │
                                                   │  └───────────────────────────────┘ │
                                                   └───────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              🗄️ DATA LAYER                                           │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                    SQLAlchemy ORM (database.py + models.py)                  │   │
│  │                                                                              │   │
│  │  User ◄──────── Enrollment ──────────► Course                               │   │
│  │   │                                      │                                  │   │
│  │   ├── UserPoints (XP/Badges)             ├── Lecture ──► LectureNote        │   │
│  │   ├── Notification                       ├── Quiz ──► QuizQuestion          │   │
│  │   ├── AITutorSession                     ├── Assignment                     │   │
│  │   ├── StudyPlan                          └── LiveClass                      │   │
│  │   ├── Certificate                                                            │   │
│  │   └── RefreshToken                      ResourceHub  ProjectCatalog         │   │
│  │                                         Internship   JobApplication         │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─────────────────────────────┐   ┌──────────────────────────────────────────────┐ │
│  │   SQLite (eduai.db)         │   │   Static File Storage                        │ │
│  │   ── Dev & Free Deployment  │   │   static/uploads/                            │ │
│  │                             │   │   ├── avatars/      (user photos)            │ │
│  │   PostgreSQL (upgrade path) │   │   ├── videos/       (course videos)          │ │
│  │   ── Production scale       │   │   ├── notes/        (PDF lecture notes)      │ │
│  └─────────────────────────────┘   │   ├── certificates/ (generated PDFs)        │ │
│                                    │   └── assignments/  (student submissions)    │ │
│                                    └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Diagram (Mermaid)

```mermaid
graph TB
    subgraph CLIENT["🖥️ Client Layer (Browser)"]
        UI_HOME[Landing Page<br/>index.html]
        UI_AUTH[Auth Pages<br/>login / register]
        UI_STUDENT[Student Dashboard<br/>dashboard.html]
        UI_FACULTY[Faculty Portal<br/>faculty.html]
        UI_ADMIN[Admin Panel<br/>admin.html]
    end

    subgraph SERVER["⚙️ FastAPI Application Server"]
        UVICORN[Uvicorn ASGI<br/>Port $PORT]
        MIDDLEWARE[Middleware Stack<br/>CORS · JWT · RateLimit]
        TEMPLATES[Jinja2 Templates<br/>HTML Page Renderer]
        STATIC[Static Files Mount<br/>/static/*]

        subgraph ROUTERS["📡 API Routers (30+)"]
            R_AUTH[/api/auth]
            R_COURSE[/api/courses]
            R_AI[/api/ai]
            R_LIVE[/api/live-class]
            R_QUIZ[/api/quizzes]
            R_CAREER[/api/careers]
            R_MORE[... 24 more]
        end
    end

    subgraph AI["🤖 AI Engine"]
        LANGCHAIN[LangChain Orchestrator]
        GEMINI[Google Gemini<br/>1.5 Flash]
        OPENAI[OpenAI GPT-3.5<br/>Fallback]
        RAG[RAG Pipeline<br/>Context Search]
        CHROMA[ChromaDB<br/>Vector Store]
        JSON_FB[JSON TF-IDF<br/>Fallback Search]
    end

    subgraph AUTH["🔐 Auth Layer"]
        JWT[JWT Tokens<br/>Access + Refresh]
        BCRYPT[BCrypt<br/>Password Hash]
        TOTP[TOTP 2FA<br/>QR Code]
    end

    subgraph DATA["🗄️ Data Layer"]
        ORM[SQLAlchemy ORM<br/>models.py]
        SQLITE[(SQLite<br/>eduai.db)]
        FILES[File Storage<br/>static/uploads/]
    end

    CLIENT --> |HTTPS fetch API| UVICORN
    UVICORN --> MIDDLEWARE
    MIDDLEWARE --> TEMPLATES
    MIDDLEWARE --> ROUTERS
    TEMPLATES --> UI_STUDENT

    R_AUTH --> AUTH
    ROUTERS --> ORM
    R_AI --> LANGCHAIN

    LANGCHAIN --> GEMINI
    LANGCHAIN --> OPENAI
    LANGCHAIN --> RAG
    RAG --> CHROMA
    RAG --> JSON_FB

    AUTH --> JWT
    AUTH --> BCRYPT
    AUTH --> TOTP

    ORM --> SQLITE
    R_COURSE --> FILES

    style CLIENT fill:#1a1a3e,color:#fff
    style SERVER fill:#0d2137,color:#fff
    style AI fill:#1a0d37,color:#fff
    style AUTH fill:#1a2d0d,color:#fff
    style DATA fill:#2d1a0d,color:#fff
```

---

## 🧩 Tech Stack Breakdown

| Layer | Technology | Purpose | Why This Choice |
|-------|-----------|---------|-----------------|
| **Web Framework** | FastAPI 0.109 | REST API + HTML serving | Async, auto-docs, type-safe, production-grade |
| **ASGI Server** | Uvicorn + Gunicorn | Production web server | Industry standard for Python async apps |
| **Template Engine** | Jinja2 3.1 | Server-side HTML rendering | Zero build step, fast, SEO-friendly |
| **ORM** | SQLAlchemy 2.0 | Database abstraction layer | Works with SQLite → PostgreSQL without code change |
| **Database (Dev)** | SQLite | Local & free-tier data store | Zero config, file-based, portable |
| **Database (Prod)** | PostgreSQL | Production-scale storage | ACID, concurrent writes, indexes |
| **AI Orchestration** | LangChain | Chain AI calls + memory | Prompt management, output parsing, RAG chains |
| **Primary LLM** | Google Gemini 1.5 Flash | AI tutor, quiz gen, study plans | Free API tier, fast, multilingual |
| **Fallback LLM** | OpenAI GPT-3.5 | Backup AI when Gemini unavailable | Most widely supported model |
| **Vector Search** | ChromaDB | Semantic document search | Local vector DB, no cloud cost |
| **RAG Fallback** | JSON + TF-IDF | Works without ChromaDB | Zero-dependency fallback for free tier |
| **Auth — Tokens** | python-jose (JWT) | Access + refresh token issuance | Industry-standard RFC 7519 |
| **Auth — Passwords** | Passlib + BCrypt | Password hashing & verification | BCrypt is industry gold standard |
| **Auth — 2FA** | PyOTP + QRCode | TOTP-based two-factor auth | Compatible with Google/MS Authenticator |
| **PDF Generation** | ReportLab | Certificate & resume PDF creation | Programmatic, no external service |
| **PDF Parsing** | PyPDF2 | Lecture note text extraction | For RAG indexing of uploaded PDFs |
| **Payments** | Stripe SDK | Course purchase processing | PCI-compliant, widely adopted |
| **Email** | aiosmtplib | Async email notifications | Non-blocking SMTP for FastAPI |
| **Rate Limiting** | SlowAPI | Protect endpoints from abuse | Fastapi-compatible, Redis/memory backend |
| **Validation** | Pydantic v2 | Request/response schemas | Zero-overhead validation, auto-docs |
| **File Uploads** | python-multipart | Multipart form data parsing | Required for FastAPI file endpoints |
| **Async Files** | aiofiles | Non-blocking file I/O | Keeps Uvicorn event loop unblocked |
| **HTTP Client** | HTTPX | External API requests | Async-first, requests-compatible |
| **WebSockets** | websockets | Live class real-time channel | RFC 6455 compliant |
| **Deployment** | Render.com | Free cloud hosting | Auto-deploy from GitHub, 0 cost |
| **Container** | Docker | Reproducible builds | Consistent dev → prod environment |
| **CI/CD** | GitHub Actions | Auto test + deploy pipeline | Free for public repos |
| **Frontend** | Vanilla HTML/CSS/JS | UI without build tools | Zero npm, zero webpack, instant deploy |
| **Fonts** | Google Fonts (Inter) | Modern UI typography | Free, fast CDN, professional look |
| **Icons** | Font Awesome 6 | UI icons throughout app | Comprehensive, CDN-delivered |

---

## 🔗 Component Connection Map

```
USER REQUEST FLOW
═════════════════

Browser
  │
  ├─ GET /login ──────────────────────────────► Jinja2 renders login.html
  │                                               └─ HTML returned to browser
  │
  ├─ POST /api/auth/login ────────────────────► auth.py router
  │    │  {email, password}                        │
  │    │                                           ├─ SQLAlchemy: query User
  │    │                                           ├─ BCrypt: verify password
  │    │                                           ├─ PyOTP: check 2FA if enabled
  │    │                                           └─ python-jose: create JWT
  │    │                                               └─ returns {access_token}
  │    │
  │    └─ Browser stores token in localStorage
  │
  ├─ GET /api/courses ────────────────────────► courses.py router
  │    Authorization: Bearer <token>               │
  │                                               ├─ auth_utils: decode JWT
  │                                               ├─ SQLAlchemy: query Course table
  │                                               └─ Pydantic: serialize response
  │
  ├─ POST /api/ai/chat ───────────────────────► ai.py router
  │    {message, course_id, history}               │
  │                                               ├─ ai_service.ai_tutor_chat()
  │                                               │   ├─ rag_service.search_course_context()
  │                                               │   │   ├─ ChromaDB similarity search
  │                                               │   │   └─ JSON TF-IDF fallback
  │                                               │   ├─ LangChain: build message chain
  │                                               │   │   SystemMessage + HumanMessage history
  │                                               │   ├─ Gemini/OpenAI: ainvoke()
  │                                               │   └─ returns AI response string
  │                                               └─ response streamed to browser
  │
  ├─ POST /api/lectures/{id}/upload-note ─────► lectures.py router
  │    multipart/form-data (PDF file)              │
  │                                               ├─ aiofiles: save to static/uploads/notes/
  │                                               ├─ models.LectureNote: DB record
  │                                               └─ rag_service.index_document()
  │                                                   ├─ PyPDF2: extract text
  │                                                   ├─ chunk_text(): split 1000-token chunks
  │                                                   └─ ChromaDB/JSON: index vectors
  │
  └─ POST /api/certificates/issue/{course_id}─► certificates.py router
       Authorization: Bearer <token>               │
                                                  ├─ Verify course completion
                                                  ├─ certificate_service.generate_pdf()
                                                  │   └─ ReportLab: create PDF bytes
                                                  ├─ aiofiles: save to static/uploads/certificates/
                                                  └─ models.Certificate: DB record


DATABASE MODEL RELATIONSHIPS
═════════════════════════════

User (1) ──────────── (N) Enrollment ──────────── (1) Course
 │                                                        │
 ├── (1) UserPoints                              (N) Lecture ──── (N) LectureNote
 ├── (N) Notification                            (N) LiveClass
 ├── (N) AITutorSession                          (N) Quiz ──────── (N) QuizQuestion
 ├── (N) StudyPlan                               (N) Assignment
 ├── (N) Certificate                             (N) Review
 ├── (N) Message
 ├── (N) UserBadge ─────── (1) Badge
 └── (N) InterviewSession


AI PIPELINE DETAIL
═══════════════════

User Message
     │
     ▼
ai_tutor_chat(message, history, course_id)
     │
     ├─[if course_id]──► rag_service.search_course_context()
     │                        │
     │                   ┌────▼─────────────────────────┐
     │                   │  Try ChromaDB semantic search │
     │                   │  ▼ (if ChromaDB available)   │
     │                   │  collection.query(            │
     │                   │    query_texts=[message],     │
     │                   │    n_results=4               │
     │                   │  )                           │
     │                   │                              │
     │                   │  Fallback: JSON TF-IDF       │
     │                   │  word overlap scoring         │
     │                   └──────────────────────────────┘
     │                        │
     │                   top-k relevant chunks
     │
     ├─► Build LangChain messages:
     │     [SystemMessage(prompt + rag_context)]
     │     [HumanMessage, AIMessage, ...] ← history[-10:]
     │     [HumanMessage(user_message)]
     │
     ├─► llm.ainvoke(messages)
     │     │
     │     ├─► Google Gemini 1.5 Flash (primary)
     │     └─► OpenAI GPT-3.5 Turbo (fallback)
     │
     └─► response.content → returned to user
```

---

## ✨ Feature Modules

<details>
<summary><b>🎓 School Education (Class 1–12)</b></summary>

- Full syllabus courses mapped to CBSE/State board
- Subject-wise video lectures, notes, and MCQ tests
- Board exam preparation with past paper analysis
- Parent progress dashboards
</details>

<details>
<summary><b>🏫 College Education (Semester 1–8)</b></summary>

- BTech / BCA / MCA semester-wise course mapping
- Lab exercises and practical guides
- Assignment submission with AI feedback
- Internal marks tracking
</details>

<details>
<summary><b>🏆 Competitive Exams</b></summary>

- UPSC, JEE, NEET, GATE, CAT preparation modules
- Daily current affairs + PYQ analysis
- Mock test engine with analytics
- Personalized AI study plans
</details>

<details>
<summary><b>💼 Career Portal & Placement</b></summary>

- 500+ live internships and job listings
- AI-powered resume builder (ReportLab PDF)
- One-click job application tracking
- Career path recommendation engine
</details>

<details>
<summary><b>🤖 AI Interview Prep</b></summary>

- Mock HR + Technical interviews with AI
- Real-time feedback on answers
- Domain-specific question banks (Web, ML, DSA, etc.)
- Confidence score and improvement tips
</details>

<details>
<summary><b>💻 Code Lab (Cloud IDE)</b></summary>

- In-browser code execution
- Language: Python, JavaScript, C, C++, Java
- Code snippet saving and sharing
- Problem sets with test case validation
</details>

<details>
<summary><b>📹 Live Classes</b></summary>

- Jitsi Meet integration (100% free video)
- Zoom / Google Meet fallback
- Auto-notify enrolled students
- Recording URL storage and playback
</details>

<details>
<summary><b>🎮 Gamification</b></summary>

- XP points on every learning action
- Level-up system (Level 1 → Grandmaster)
- Streak tracking (daily learning)
- Badge awards and leaderboard
</details>

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.11+    # Runtime
Git             # Version control
```

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/AkarshYash/Skill-Sharp-LMS-Final.git
cd Skill-Sharp-LMS-Final

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY for AI features

# 5. Seed the database with sample data
python seed.py

# 6. Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 7. Open browser
# Homepage:  http://localhost:8000
# API Docs:  http://localhost:8000/api/docs
```

### Docker

```bash
docker build -t skillsharp365 .
docker run -p 8000:8000 --env-file .env skillsharp365
```

---

## 🔑 Test Credentials

> 🌐 Live at: **https://skill-sharp-lms.onrender.com/login**
>
> Click the **"Use"** button next to any test account on the login page!

| Role | Email | Password | Dashboard |
|------|-------|----------|-----------|
| 👑 **Admin** | `admin@skillssharp365.com` | `Admin@123` | `/admin` |
| 👩‍🏫 **Teacher** | `teacher@skillssharp365.com` | `Teacher@123` | `/faculty` |
| 🎓 **Student** | `student@skillssharp365.com` | `Student@123` | `/dashboard` |

---

## 📡 API Reference

| Module | Endpoint | Method | Description |
|--------|----------|--------|-------------|
| **Auth** | `/api/auth/register` | POST | Register new account |
| **Auth** | `/api/auth/login` | POST | Login, get JWT tokens |
| **Auth** | `/api/auth/refresh` | POST | Refresh access token |
| **Auth** | `/api/auth/2fa/setup` | POST | Set up TOTP 2FA |
| **Users** | `/api/users/me` | GET | Get current user profile |
| **Users** | `/api/users/{id}` | PUT | Update profile + avatar |
| **Courses** | `/api/courses` | GET | List all courses (with filters) |
| **Courses** | `/api/courses` | POST | Create course (faculty) |
| **Lectures** | `/api/lectures/{course_id}` | GET | Get course lectures |
| **Lectures** | `/api/lectures/{id}/upload-note` | POST | Upload PDF note (RAG indexed) |
| **AI** | `/api/ai/chat` | POST | AI tutor chat with RAG context |
| **AI** | `/api/ai/generate-quiz` | POST | AI quiz generation |
| **AI** | `/api/ai/study-plan` | POST | AI personalized study plan |
| **AI** | `/api/ai/solve-doubt` | POST | Instant doubt solving |
| **Live Class** | `/api/live-class` | GET | List upcoming live sessions |
| **Live Class** | `/api/live-class` | POST | Schedule new live class |
| **Quizzes** | `/api/quizzes` | GET | Get quizzes for course |
| **Quizzes** | `/api/quizzes/{id}/attempt` | POST | Submit quiz attempt |
| **Analytics** | `/api/analytics/student` | GET | Student learning analytics |
| **Analytics** | `/api/analytics/faculty` | GET | Course + student insights |
| **Gamification** | `/api/gamification/leaderboard` | GET | Top learners leaderboard |
| **Certificates** | `/api/certificates/issue/{id}` | POST | Issue course certificate |
| **Career** | `/api/careers` | GET | List job/internship listings |
| **Career** | `/api/careers/apply/{id}` | POST | Apply for a position |
| **Interview** | `/api/interview/start` | POST | Start AI mock interview |
| **Code Lab** | `/api/code-lab/execute` | POST | Execute code snippet |
| **Payments** | `/api/payments/create-intent` | POST | Create Stripe payment |
| **Admin** | `/api/admin/users` | GET | All platform users |
| **Admin** | `/api/admin/analytics` | GET | Platform-wide stats |
| **Health** | `/health` | GET | Server health check |

> 📖 **Full interactive docs:** https://skill-sharp-lms.onrender.com/api/docs

---

## 🗂️ Project Structure

```
Skill-Sharp-LMS-Final/
│
├── main.py                 # FastAPI app init, all router registration, HTML page routes
├── config.py               # Pydantic Settings — all env variables in one place
├── database.py             # SQLAlchemy engine, session factory, get_db dependency
├── models.py               # All 40+ SQLAlchemy ORM models (User, Course, Quiz, etc.)
├── auth_utils.py           # JWT encode/decode, BCrypt, require_role() decorator
├── seed.py                 # Database seed script (users, courses, lectures, jobs)
│
├── routers/                # 30 API router modules
│   ├── auth.py             # Register, login, logout, 2FA, token refresh
│   ├── users.py            # Profile CRUD, avatar upload
│   ├── courses.py          # Course CRUD, enrollment, search, filtering
│   ├── lectures.py         # Lecture management, PDF note upload, RAG indexing
│   ├── quizzes.py          # Quiz CRUD, attempt submission, leaderboard
│   ├── assignments.py      # Assignment create/submit, AI feedback trigger
│   ├── ai.py               # AI chat, quiz gen, study plan, doubt solver
│   ├── live_class.py       # Live class scheduling, Jitsi link generation
│   ├── analytics.py        # Student/faculty/admin analytics endpoints
│   ├── gamification.py     # XP, badges, streaks, leaderboard
│   ├── certificates.py     # Certificate issuance, PDF generation
│   ├── career.py           # Internships, job listings
│   ├── career_portal.py    # Advanced career portal with applications
│   ├── interview.py        # AI mock interview sessions
│   ├── interview_prep.py   # Interview prep resources and tips
│   ├── code_lab.py         # Cloud code execution, snippet management
│   ├── school_education.py # School-specific modules
│   ├── college_education.py# College semester modules
│   ├── competitive_exams.py# UPSC/JEE/NEET prep modules
│   ├── professional_courses.py # Paid pro course handling
│   ├── study_plan.py       # Personalized study plan management
│   ├── resume.py           # AI resume generation + PDF export
│   ├── payments.py         # Stripe payment intents
│   ├── chat.py             # Student-to-faculty direct messaging
│   ├── notifications.py    # In-app notification system
│   ├── admin.py            # Admin panel — users, content moderation, stats
│   ├── groups.py           # Study group creation and chat
│   ├── resources.py        # Resource hub (links, docs)
│   ├── projects.py         # Project catalog with playlist
│   └── jobseekers.py       # Jobseeker profile and matching
│
├── services/
│   ├── ai_service.py       # LangChain + Gemini/OpenAI — all AI logic
│   ├── rag_service.py      # RAG pipeline — ChromaDB + JSON fallback search
│   └── certificate_service.py # ReportLab PDF certificate generator
│
├── templates/              # Jinja2 HTML templates
│   ├── index.html          # Landing page with hero, features, reviews
│   ├── login.html          # Login with demo accounts
│   ├── register.html       # Multi-role registration
│   ├── dashboard.html      # Student dashboard (courses, AI, quizzes)
│   ├── faculty.html        # Faculty portal (course mgmt, live class)
│   ├── admin.html          # Admin control panel
│   ├── courses.html        # Course browse/enroll page
│   └── verify.html         # Email verification page
│
├── static/
│   ├── images/             # Hero, gallery, and UI images
│   └── uploads/            # User-generated content (avatars, videos, PDFs)
│       ├── avatars/
│       ├── videos/
│       ├── notes/
│       ├── certificates/
│       ├── assignments/
│       └── files/
│
├── chroma_db/              # ChromaDB vector store (created at runtime)
├── render.yaml             # Render.com deployment config
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Multi-service Docker setup (with nginx)
├── nginx.conf              # Nginx reverse proxy config
├── requirements.txt        # Python dependencies (pinned versions)
├── .env.example            # Environment variables template
└── .gitignore              # Excludes venv, .env, *.db, __pycache__
```

---

## 🌐 Deployment Guide

### 🆓 Render.com (Free — Recommended)

1. Fork this repo to your GitHub account
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your forked repo
4. Use these settings:

```
Name:          skill-sharp-lms
Runtime:       Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

5. Add environment variables:
```
SECRET_KEY   = <any long random string>
DATABASE_URL = sqlite:///./eduai.db
GEMINI_API_KEY = <optional — get free at aistudio.google.com>
```

6. Click **Deploy** — your app will be live at `https://your-app.onrender.com` in ~5 minutes!

> ⚠️ Free tier sleeps after 15 min inactivity. First wake-up takes ~30 seconds.

---

### 🐋 Docker Self-Host

```bash
# Build
docker build -t skillsharp365 .

# Run with env vars
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="your_secret_here" \
  -e GEMINI_API_KEY="your_gemini_key" \
  --name skillsharp365 \
  skillsharp365
```

---

### 🌩️ Production (VPS / AWS EC2)

```bash
# Install dependencies
sudo apt update && sudo apt install python3.11 python3-pip nginx -y

# Clone and setup
git clone https://github.com/AkarshYash/Skill-Sharp-LMS-Final.git
cd Skill-Sharp-LMS-Final
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Setup nginx as reverse proxy (use nginx.conf in repo)
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

```bash
# 1. Fork the repo
# 2. Create a feature branch
git checkout -b feature/your-amazing-feature

# 3. Make your changes
# 4. Test locally
python -m pytest

# 5. Push and open a Pull Request
git push origin feature/your-amazing-feature
```

### Areas We'd Love Help With
- 🌍 Multilingual support (Hindi, Tamil, Telugu)
- 📱 Progressive Web App (PWA) support
- 🔔 Push notifications
- 📊 Advanced analytics dashboards
- 🎥 HLS video streaming integration

---

## 📜 License

This project is licensed under the **MIT License** — free for personal and commercial use.

---

<div align="center">

### 🌟 If this project helped you, please give it a star!

[![Star this repo](https://img.shields.io/github/stars/AkarshYash/Skill-Sharp-LMS-Final?style=social)](https://github.com/AkarshYash/Skill-Sharp-LMS-Final)

**Built with ❤️ by [Akarsh Chaturvedi](https://github.com/AkarshYash)**

[![Live Demo](https://img.shields.io/badge/🚀_Try_It_Now-skill--sharp--lms.onrender.com-6c63ff?style=for-the-badge)](https://skill-sharp-lms.onrender.com)

</div>
