"""
Certificate Service — PDF Generation using ReportLab
Generates professional, styled certificates for course completion
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os
import qrcode
import tempfile
from reportlab.lib.utils import ImageReader

PRIMARY   = HexColor("#6366f1")   # Indigo
GOLD      = HexColor("#f59e0b")   # Gold
DARK      = HexColor("#1e1b4b")   # Dark navy
ACCENT    = HexColor("#a5b4fc")   # Light indigo

def generate_certificate_pdf(
    student_name: str,
    course_title: str,
    faculty_name: str,
    verify_code:  str,
    output_path:  str,
    issue_date:   str = None
):
    """Generate a beautiful PDF certificate"""
    if not issue_date:
        issue_date = datetime.utcnow().strftime("%B %d, %Y")
    
    # Landscape A4
    width, height = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    
    # ── Background gradient effect ──────────────────
    c.setFillColor(DARK)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Decorative border overlay
    c.setFillColor(HexColor("#2d2a6e"))
    c.rect(15, 15, width - 30, height - 30, fill=1, stroke=0)
    
    # Gold border
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.rect(25, 25, width - 50, height - 50, fill=0, stroke=1)
    c.setLineWidth(1)
    c.rect(32, 32, width - 64, height - 64, fill=0, stroke=1)
    
    # Corner decorations
    for (x, y) in [(40, height-40), (width-40, height-40), (40, 40), (width-40, 40)]:
        c.setFillColor(GOLD)
        c.circle(x, y, 6, fill=1, stroke=0)
    
    # ── Header ──────────────────────────────────────
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width/2, height - 70, "SKILLS SHARP 365 INNOVATION")
    
    c.setFillColor(ACCENT)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 87, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # ── Main Title ──────────────────────────────────
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width/2, height - 118, "CERTIFICATE OF COMPLETION")
    
    # ── Subtitle ────────────────────────────────────
    c.setFillColor(ACCENT)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 140, "This is to certify that")
    
    # ── Student Name ────────────────────────────────
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width/2, height - 195, student_name)
    
    # Underline
    name_width = c.stringWidth(student_name, "Helvetica-Bold", 32)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(width/2 - name_width/2 - 20, height - 205, width/2 + name_width/2 + 20, height - 205)
    
    # ── Course Title ─────────────────────────────────
    c.setFillColor(white)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width/2, height - 235, "has successfully completed the course")
    
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 18)
    # Word wrap for long titles
    if len(course_title) > 50:
        mid = len(course_title) // 2
        space = course_title.rfind(" ", 0, mid)
        line1 = course_title[:space]
        line2 = course_title[space+1:]
        c.drawCentredString(width/2, height - 265, line1)
        c.drawCentredString(width/2, height - 287, line2)
        bottom_y = height - 310
    else:
        c.drawCentredString(width/2, height - 265, course_title)
        bottom_y = height - 295
    
    # ── Divider ─────────────────────────────────────
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.5)
    c.line(width/2 - 150, bottom_y - 10, width/2 + 150, bottom_y - 10)
    
    # ── Footer info ─────────────────────────────────
    footer_y = bottom_y - 45
    
    # Issue Date
    c.setFillColor(ACCENT)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/4, footer_y + 15, "ISSUED ON")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width/4, footer_y, issue_date)
    
    # Faculty
    c.setFillColor(ACCENT)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, footer_y + 15, "INSTRUCTOR")
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width/2, footer_y, faculty_name)
    
    # Verify Code
    c.setFillColor(ACCENT)
    c.setFont("Helvetica", 9)
    c.drawCentredString(3*width/4, footer_y + 15, "VERIFY CODE")
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(3*width/4, footer_y, verify_code)
    
    # Signature lines
    sig_y = footer_y - 30
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.5)
    for x in [width/4, width/2, 3*width/4]:
        c.line(x - 60, sig_y, x + 60, sig_y)
    
    # ── Bottom watermark ────────────────────────────
    c.setFillColor(HexColor("#4338ca"))
    c.setFont("Helvetica", 7)
    verify_url = f"skillssharp365.com/verify/{verify_code}"
    c.drawCentredString(width/2, 38, f"Verify this certificate at: {verify_url}")
    
    # ── QR Code ─────────────────────────────────────
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(f"https://{verify_url}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img.save(tmp.name)
        c.drawImage(ImageReader(tmp.name), 60, 60, width=60, height=60)
    os.unlink(tmp.name)
    
    c.save()
    return output_path
