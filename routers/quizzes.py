from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

class QuizCreate(BaseModel):
    course_id: str
    title: str
    description: Optional[str] = None
    time_limit: int = 30
    passing_score: int = 60
    max_attempts: int = 3
    lecture_id: Optional[str] = None

class QuestionCreate(BaseModel):
    question: str
    type: str = "mcq"
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    marks: int = 1
    order_index: int = 0

class QuizAttemptSubmit(BaseModel):
    answers: dict   # {question_id: answer}
    time_taken: int = 0

class AIQuizRequest(BaseModel):
    course_id: str
    lecture_id: Optional[str] = None
    topic: str
    num_questions: int = 10
    difficulty: str = "medium"

def quiz_dict(q: models.Quiz) -> dict:
    return {
        "id":           q.id,
        "course_id":    q.course_id,
        "title":        q.title,
        "description":  q.description,
        "time_limit":   q.time_limit,
        "passing_score": q.passing_score,
        "max_attempts": q.max_attempts,
        "is_published": q.is_published,
        "ai_generated": q.ai_generated,
        "question_count": len(q.questions),
        "created_at":   str(q.created_at),
    }

@router.get("/course/{course_id}")
def get_course_quizzes(
    course_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(models.Quiz).filter(
        models.Quiz.course_id == course_id,
        models.Quiz.is_published == True
    ).all()
    result = []
    for quiz in q:
        d = quiz_dict(quiz)
        # Check attempts
        attempts = db.query(models.QuizAttempt).filter(
            models.QuizAttempt.quiz_id    == quiz.id,
            models.QuizAttempt.student_id == user.id
        ).count()
        d["attempts_made"] = attempts
        d["can_attempt"]   = attempts < quiz.max_attempts
        result.append(d)
    return result

@router.post("/")
def create_quiz(
    data: QuizCreate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    quiz = models.Quiz(**data.model_dump())
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz_dict(quiz)

@router.post("/{quiz_id}/questions")
def add_question(
    quiz_id: str,
    data: QuestionCreate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    
    q = models.QuizQuestion(quiz_id=quiz_id, **data.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return {
        "id":          q.id,
        "question":    q.question,
        "type":        q.type,
        "options":     q.options,
        "marks":       q.marks,
        "order_index": q.order_index,
    }

@router.get("/{quiz_id}")
def get_quiz(
    quiz_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    
    data = quiz_dict(quiz)
    questions = []
    for q in sorted(quiz.questions, key=lambda x: x.order_index):
        qd = {
            "id":       q.id,
            "question": q.question,
            "type":     q.type,
            "options":  q.options,
            "marks":    q.marks,
        }
        # Only include correct_answer for faculty/admin
        if user.role in ["faculty", "admin"]:
            qd["correct_answer"] = q.correct_answer
            qd["explanation"]    = q.explanation
        questions.append(qd)
    data["questions"] = questions
    return data

@router.post("/{quiz_id}/submit")
def submit_quiz(
    quiz_id: str,
    data: QuizAttemptSubmit,
    user: models.User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    
    attempts = db.query(models.QuizAttempt).filter(
        models.QuizAttempt.quiz_id    == quiz_id,
        models.QuizAttempt.student_id == user.id
    ).count()
    if attempts >= quiz.max_attempts:
        raise HTTPException(400, "Max attempts reached")
    
    # Grade the quiz
    questions = quiz.questions
    total_marks = sum(q.marks for q in questions)
    earned      = 0
    wrong_topics = []
    
    for q in questions:
        user_ans = data.answers.get(q.id, "")
        if str(user_ans).strip().lower() == str(q.correct_answer).strip().lower():
            earned += q.marks
        else:
            wrong_topics.append(q.question[:50])
    
    score_pct = int((earned / total_marks * 100)) if total_marks > 0 else 0
    passed    = score_pct >= quiz.passing_score
    
    attempt = models.QuizAttempt(
        quiz_id    = quiz_id,
        student_id = user.id,
        answers    = data.answers,
        score      = score_pct,
        max_score  = 100,
        passed     = passed,
        time_taken = data.time_taken
    )
    db.add(attempt)
    
    # Award XP
    pts = user.points
    if pts:
        xp_gain = score_pct // 10 * 5  # up to 50 XP
        pts.xp += xp_gain
    
    db.commit()
    
    return {
        "score":       score_pct,
        "passed":      passed,
        "earned_marks": earned,
        "total_marks": total_marks,
        "wrong_topics": wrong_topics[:3],
        "message": "🎉 Passed! Great job!" if passed else f"Score: {score_pct}%. Need {quiz.passing_score}% to pass. Keep trying!"
    }

@router.get("/{quiz_id}/results")
def get_quiz_results(
    quiz_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attempts = db.query(models.QuizAttempt).filter(
        models.QuizAttempt.quiz_id    == quiz_id,
        models.QuizAttempt.student_id == user.id
    ).order_by(models.QuizAttempt.attempted_at.desc()).all()
    
    return [
        {
            "id":          a.id,
            "score":       a.score,
            "passed":      a.passed,
            "time_taken":  a.time_taken,
            "attempted_at": str(a.attempted_at),
        }
        for a in attempts
    ]

@router.post("/ai-generate")
async def generate_ai_quiz(
    data: AIQuizRequest,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    try:
        from services.ai_service import generate_quiz_questions
        questions = await generate_quiz_questions(data.topic, data.num_questions, data.difficulty)
        
        # Create quiz
        quiz = models.Quiz(
            course_id    = data.course_id,
            lecture_id   = data.lecture_id,
            title        = f"AI Quiz: {data.topic}",
            description  = f"Auto-generated quiz on {data.topic}",
            ai_generated = True
        )
        db.add(quiz)
        db.flush()
        
        for i, q in enumerate(questions):
            qq = models.QuizQuestion(
                quiz_id        = quiz.id,
                question       = q["question"],
                type           = "mcq",
                options        = q.get("options", []),
                correct_answer = q["answer"],
                explanation    = q.get("explanation", ""),
                marks          = 1,
                order_index    = i
            )
            db.add(qq)
        
        db.commit()
        return {"quiz_id": quiz.id, "title": quiz.title, "questions_count": len(questions)}
    except Exception as e:
        raise HTTPException(500, f"AI quiz generation failed: {str(e)}")
