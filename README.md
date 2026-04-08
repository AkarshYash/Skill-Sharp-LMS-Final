# EduAI – AI-Powered E-Learning Platform

## Quick Start

### Prerequisites
- Node.js 20+
- PostgreSQL 15+
- Redis
- Docker (optional)

### 1. Clone & Setup

```bash
# Backend
cd backend
cp .env.example .env   # Fill in your keys
npm install
npm run migrate        # Run DB schema
npm run dev

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### 2. Docker (Recommended)

```bash
cp backend/.env.example backend/.env  # Fill in your keys
docker-compose up -d
```

Visit: http://localhost:3000

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret for access tokens |
| `GEMINI_API_KEY` | Google Gemini AI key |
| `OPENAI_API_KEY` | OpenAI key (fallback) |
| `STRIPE_SECRET_KEY` | Stripe payments |
| `SMTP_*` | Email configuration |

---

## Architecture

```
elearning-platform/
├── backend/              Node.js + Express + Socket.io
│   ├── src/
│   │   ├── routes/       REST API endpoints
│   │   ├── db/           PostgreSQL schema & migrations
│   │   ├── middleware/   Auth, upload, rate limiting
│   │   ├── socket/       Real-time WebSocket handlers
│   │   └── utils/        JWT, email, logger
├── frontend/             Next.js 14 + TailwindCSS
│   └── src/
│       ├── app/          Pages (App Router)
│       ├── components/   Reusable UI components
│       ├── store/        Zustand state management
│       └── lib/          API client
├── docker-compose.yml
└── nginx.conf
```

---

## API Endpoints

| Module | Base Path |
|---|---|
| Auth | `POST /api/auth/register`, `/login`, `/refresh` |
| Courses | `GET/POST /api/courses` |
| AI Guide | `POST /api/ai/chat`, `/solve-doubt`, `/study-plan` |
| Quizzes | `GET/POST /api/quizzes` |
| Chat | `GET/POST /api/chat/messages/:userId` |
| Certificates | `POST /api/certificates/issue/:courseId` |
| Gamification | `GET /api/gamification/leaderboard` |
| Analytics | `GET /api/analytics/student` |
| Payments | `POST /api/payments/create-intent` |
| Career | `GET /api/career/internships` |

---

## Roles

- **Student** – Enroll, learn, quiz, chat, earn certificates
- **Faculty** – Create courses, host live classes, grade assignments
- **Admin** – Full platform management, analytics, user control

---

## Deployment

```bash
# Build & push to AWS ECR, deploy via ECS
# CI/CD via GitHub Actions (.github/workflows/ci-cd.yml)
```
