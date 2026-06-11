from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from auth_utils import require_role
from config import settings
import models

router = APIRouter()

class PaymentCreate(BaseModel):
    course_id: str
    amount:    float
    currency:  str = "usd"

@router.post("/create-checkout")
async def create_checkout(
    data: PaymentCreate,
    user_id: str,
    db: Session = Depends(get_db)
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(503, "Payments not configured")
    
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        course = db.query(models.Course).filter(models.Course.id == data.course_id).first()
        if not course:
            raise HTTPException(404, "Course not found")
        
        session = stripe.checkout.Session.create(
            payment_method_types = ["card"],
            line_items = [{
                "price_data": {
                    "currency":     data.currency,
                    "product_data": {"name": course.title},
                    "unit_amount":  int(data.amount * 100),
                },
                "quantity": 1,
            }],
            mode        = "payment",
            success_url = f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url  = f"{settings.FRONTEND_URL}/courses/{data.course_id}",
            metadata    = {"course_id": data.course_id, "user_id": user_id}
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/webhook")
async def stripe_webhook(request_data: dict, db: Session = Depends(get_db)):
    # Handle successful payment
    if request_data.get("type") == "checkout.session.completed":
        metadata  = request_data["data"]["object"]["metadata"]
        course_id = metadata.get("course_id")
        user_id   = metadata.get("user_id")
        amount    = request_data["data"]["object"]["amount_total"] / 100
        
        # Record payment
        payment = models.Payment(
            student_id = user_id,
            course_id  = course_id,
            stripe_id  = request_data["data"]["object"]["id"],
            amount     = amount,
            status     = "succeeded"
        )
        db.add(payment)
        
        # Auto-enroll
        existing = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == user_id,
            models.Enrollment.course_id  == course_id
        ).first()
        if not existing:
            enrollment = models.Enrollment(student_id=user_id, course_id=course_id)
            db.add(enrollment)
            course = db.query(models.Course).filter(models.Course.id == course_id).first()
            if course:
                course.total_students += 1
        
        db.commit()
    return {"status": "ok"}
