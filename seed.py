"""
seed.py - High-fidelity database seeding script for Skill Sharp 365 Innovations LMS
Populates users, courses, lectures, live classes, career postings, gamification points, and RAG vector caches.
Unicode-safe for all Windows console environments.
"""
import os
import sys
import json
import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
from auth_utils import hash_password

# Reconfigure stdout to prevent encoding errors on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def seed_database():
    print("====================================================")
    print("      Skill Sharp 365 Innovations -- Database Seed")
    print("====================================================")
    
    # Initialize connection
    db = SessionLocal()
    
    # Ensure all tables exist (safe to run on existing DB)
    Base.metadata.create_all(bind=engine)
    
    # ─── IDEMPOTENT CHECK ───────────────────────────────
    # If admin account already exists with correct password, skip full re-seed
    existing_admin = db.query(models.User).filter(models.User.email == "admin@skillssharp365.com").first()
    if existing_admin:
        from auth_utils import verify_password
        if verify_password("Admin@123", existing_admin.password):
            print("[OK] Database already seeded with correct credentials — skipping re-seed.")
            db.close()
            return
        else:
            print("[INFO] Admin found but password mismatch — re-seeding with correct credentials...")
    else:
        print("[INFO] No seed data found — seeding fresh database...")
    
    print("\n[1/6] Cleaning up old database tables...")

    try:
        db.query(models.JobApplication).delete()
        db.query(models.CodeSnippet).delete()
        db.query(models.InterviewSession).delete()
        db.query(models.RAGDocument).delete()
        db.query(models.Payment).delete()
        db.query(models.Internship).delete()
        db.query(models.LiveClass).delete()
        db.query(models.AITutorSession).delete()
        db.query(models.StudyPlan).delete()
        db.query(models.UserBadge).delete()
        db.query(models.Badge).delete()
        db.query(models.UserPoints).delete()
        db.query(models.Review).delete()
        db.query(models.Certificate).delete()
        db.query(models.Notification).delete()
        db.query(models.Message).delete()
        db.query(models.AssignmentSubmission).delete()
        db.query(models.Assignment).delete()
        db.query(models.QuizAttempt).delete()
        db.query(models.QuizQuestion).delete()
        db.query(models.Quiz).delete()
        db.query(models.LectureProgress).delete()
        db.query(models.LectureNote).delete()
        db.query(models.Lecture).delete()
        db.query(models.Enrollment).delete()
        db.query(models.Course).delete()
        db.query(models.User).delete()
        db.commit()
        print("[OK] Database wiped successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error cleaning database: {e}")
        return

    print("\n[2/6] Seeding standard user credentials...")
    try:
        # Create standard student
        student = models.User(
            name="Akarsh Chaturvedi",
            email="student@skillssharp365.com",
            password=hash_password("Student@123"),
            role="student",
            student_type="college",
            class_grade="Semester 1",
            bio="Aspiring full-stack engineer and AI specialist. Learning, practicing, and building every day!",
            avatar="A",
            is_verified=True
        )
        db.add(student)
        
        # Create faculty
        teacher = models.User(
            name="Dr. Sarah Jenkins",
            email="teacher@skillssharp365.com",
            password=hash_password("Teacher@123"),
            role="faculty",
            expertise="Artificial Intelligence, Computer Science Foundations",
            bio="Professor of Computer Science with 12+ years of research and teaching experience.",
            avatar="S",
            is_verified=True
        )
        db.add(teacher)
        
        # Create admin
        admin = models.User(
            name="Administrator",
            email="admin@skillssharp365.com",
            password=hash_password("Admin@123"),
            role="admin",
            bio="Skill Sharp 365 Innovations Platform Administration.",
            avatar="A",
            is_verified=True
        )
        db.add(admin)
        db.flush() # flush to get primary key IDs
        
        # Create Gamification Points for Student
        points = models.UserPoints(
            user_id=student.id,
            xp=380,
            level=3,
            streak_days=5,
            longest_streak=12,
            last_activity="Seeded Login"
        )
        db.add(points)
        
        # Add Achievements Badges
        b1 = models.Badge(name="First Step", description="Enroll in your first course", icon="A", condition_type="xp_earned", condition_value=10, color="#6366f1")
        b2 = models.Badge(name="Code Warrior", description="Write and run code in the Cloud IDE", icon="B", condition_type="xp_earned", condition_value=100, color="#06b6d4")
        b3 = models.Badge(name="Interview Ready", description="Complete an AI Mock Interview simulation", icon="C", condition_type="xp_earned", condition_value=250, color="#10b981")
        db.add_all([b1, b2, b3])
        db.flush()
        
        # Assign badges to student
        db.add(models.UserBadge(user_id=student.id, badge_id=b1.id))
        db.add(models.UserBadge(user_id=student.id, badge_id=b2.id))
        
        print(f"[OK] Users seeded: {student.email} (Student), {teacher.email} (Faculty), {admin.email} (Admin)")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding users: {e}")
        return

    print("\n[3/6] Seeding learning modules & courses...")
    try:
        # --- SCHOOL COURSES (Class 10) ---
        c_math = models.Course(
            title="Class 10 Mathematics",
            description="A complete syllabus guide for Class 10 board exam preparation in Mathematics. Covers core formulas, step-by-step notes, exercises, and practice questions for Algebra, Geometry, and Trigonometry.",
            short_desc="Master Algebra, Geometry, and Trigonometry for Class 10 board exams.",
            category="Mathematics",
            level="beginner",
            price=0,
            student_type="school",
            class_grade="Class 10",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.8,
            total_students=340
        )
        c_science = models.Course(
            title="Class 10 Science",
            description="Comprehensive study notes, video lectures, and MCQs covering Physics (Light, Electricity), Chemistry (Chemical Reactions, Acids and Bases), and Biology (Life Processes, Heredity) for Class 10.",
            short_desc="Physics, Chemistry, and Biology foundation for Class 10.",
            category="Science (Physics/Chem/Bio)",
            level="beginner",
            price=0,
            student_type="school",
            class_grade="Class 10",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.7,
            total_students=280
        )
        c_languages = models.Course(
            title="Class 10 Languages",
            description="Improve language comprehension, writing skills, and grammar fundamentals in English literature and Hindi for board prep.",
            short_desc="English literature, grammar, and Hindi syllabus.",
            category="Languages (English/Hindi)",
            level="beginner",
            price=0,
            student_type="school",
            class_grade="Class 10",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.5,
            total_students=120
        )
        c_social = models.Course(
            title="Class 10 Social Studies",
            description="Engaging history timelines, geography maps, civics rights, and basic economic modules mapped exactly to the Class 10 curriculum.",
            short_desc="History, Civics, Geography, and Economics.",
            category="Social Studies",
            level="beginner",
            price=0,
            student_type="school",
            class_grade="Class 10",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.6,
            total_students=190
        )
        
        # --- COLLEGE COURSES (BTech CSE Semesters 1-3) ---
        c_prog = models.Course(
            title="Computer Programming in C",
            description="Fundamental course on computer programming using C language. Includes programming control structures (if-else, switch, while, for loops), arrays, string parsing, custom structures, functions, pointers, and file operations. Designed specifically for BTech CSE Semester 1.",
            short_desc="Learn basic loops, arrays, structures, pointers, and file handling in C.",
            category="BTech CSE",
            level="beginner",
            price=0,
            student_type="college",
            class_grade="Semester 1",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.9,
            total_students=450
        )
        c_phys = models.Course(
            title="Engineering Physics",
            description="Advanced BTech physics course covering mechanics, wave optics, electromagnetism, lasers, fiber optic communications, and modern quantum principles.",
            short_desc="Mechanics, wave optics, electromagnetism, and modern quantum physics.",
            category="BTech CSE",
            level="intermediate",
            price=0,
            student_type="college",
            class_grade="Semester 1",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.4,
            total_students=310
        )
        c_dsa = models.Course(
            title="Data Structures & Algorithms",
            description="Core BTech CSE Semester 2 syllabus. In-depth training on linear data structures (arrays, stacks, queues, linked lists), non-linear data structures (binary trees, BSTs, AVL trees, graphs), sorting/searching algorithms, and asymptotic complexity analysis.",
            short_desc="Stacks, Queues, Linked Lists, Trees, Graphs, Sorting, and Searching.",
            category="BTech CSE",
            level="intermediate",
            price=0,
            student_type="college",
            class_grade="Semester 2",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.9,
            total_students=580
        )
        c_oop = models.Course(
            title="Object Oriented Programming with C++",
            description="Master object-oriented design and C++ programming: classes, dynamic objects, constructors/destructors, inheritance, polymorphism, operator overloading, encapsulation, and Standard Template Library (STL).",
            short_desc="OOP principles: inheritance, polymorphism, templates, and STL.",
            category="BTech CSE",
            level="intermediate",
            price=0,
            student_type="college",
            class_grade="Semester 3",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.8,
            total_students=380
        )
        c_dbms = models.Course(
            title="Database Management Systems",
            description="Relational database concepts, ER diagrams, normalization (1NF to BCNF), structured query language (SQL select, join, subqueries), transaction control properties (ACID), and database indexing structures.",
            short_desc="Relational DB, SQL, normalization, transactions, and indexing.",
            category="BTech CSE",
            level="intermediate",
            price=0,
            student_type="college",
            class_grade="Semester 3",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.7,
            total_students=410
        )

        # --- PROFESSIONAL MARKETPLACE COURSES ---
        c_ai = models.Course(
            title="AI Engineering & Large Language Models",
            description="Learn to build context-aware AI applications using LangChain, Retrieval-Augmented Generation (RAG) pipelines, ChromaDB vector stores, fine-tuning OpenAI/Gemini models, and deploying Agentic AI workflows.",
            short_desc="Master LangChain, RAG pipelines, fine-tuning, and Agentic AI workflows.",
            category="Artificial Intelligence",
            level="advanced",
            price=49.99,
            student_type="professional",
            class_grade="",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.95,
            total_students=850
        )
        c_mern = models.Course(
            title="MERN Stack Development Bootcamp",
            description="Build and deploy full-stack industrial-grade applications using MongoDB, Express, React, and Node.js. Includes Redux, JWT security, and Docker packaging.",
            short_desc="Full-stack web application development with MongoDB, Express, React, and Node.",
            category="Web Development",
            level="intermediate",
            price=29.99,
            student_type="professional",
            class_grade="",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.8,
            total_students=1200
        )
        
        # --- COMPETITIVE EXAMS ---
        c_upsc = models.Course(
            title="UPSC Civil Services Foundation Prep",
            description="Comprehensive foundation guide mapping the UPSC CSE Prelims and Mains exams. Includes Indian Polity & Constitution, Modern History, Geography, and Current Affairs briefs.",
            short_desc="Comprehensive syllabus coverage for UPSC Prelims and Mains (History, Polity, Geography).",
            category="Competitive Exams",
            level="beginner",
            price=0,
            student_type="professional",
            class_grade="",
            faculty_id=teacher.id,
            is_published=True,
            approval_status="approved",
            rating=4.9,
            total_students=2400
        )

        db.add_all([c_math, c_science, c_languages, c_social, c_prog, c_phys, c_dsa, c_oop, c_dbms, c_ai, c_mern, c_upsc])
        db.flush()
        print("[OK] Educational courses seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding courses: {e}")
        return

    print("\n[4/6] Seeding course lectures & enrollments...")
    try:
        # Enroll Student in a few BTech courses
        db.add(models.Enrollment(student_id=student.id, course_id=c_prog.id, progress=45))
        db.add(models.Enrollment(student_id=student.id, course_id=c_dsa.id, progress=20))
        db.add(models.Enrollment(student_id=student.id, course_id=c_ai.id, progress=10))
        
        # Add lectures for C programming
        l_c1 = models.Lecture(
            course_id=c_prog.id, title="Introduction to C & Flow Control",
            description="Discusses compilation lifecycle, variables, data types, and using if-else and switch control blocks.",
            video_url="https://www.youtube.com/embed/zuegQmMdy8M", video_type="youtube", duration=1200, order_index=1
        )
        l_c2 = models.Lecture(
            course_id=c_prog.id, title="Understanding Pointers & Memory Address",
            description="Explains pointers, dereferencing variables, pass-by-value vs pass-by-reference, and memory layouts.",
            video_url="https://www.youtube.com/embed/rtgYl5a1ZlY", video_type="youtube", duration=1800, order_index=2
        )
        
        # Add lectures for DSA
        l_d1 = models.Lecture(
            course_id=c_dsa.id, title="Introduction to Linked Lists",
            description="Explains dynamic linear node allocation, singly vs doubly linked list traversals, inserts and deletions.",
            video_url="https://www.youtube.com/embed/zuegQmMdy8M", video_type="youtube", duration=1500, order_index=1
        )
        l_d2 = models.Lecture(
            course_id=c_dsa.id, title="Binary Search Trees Traversals",
            description="Visualizes root node structures, BST properties, and Pre-order, In-order, Post-order traversal loops.",
            video_url="https://www.youtube.com/embed/rtgYl5a1ZlY", video_type="youtube", duration=2100, order_index=2
        )
        
        # Add lectures for Class 10 Math
        l_m1 = models.Lecture(
            course_id=c_math.id, title="Quadratic Equations Fundamentals",
            description="Covers equations definition, finding roots via factorization and using the discriminant formula D = b^2 - 4ac.",
            video_url="https://www.youtube.com/embed/zuegQmMdy8M", video_type="youtube", duration=900, order_index=1
        )
        l_m2 = models.Lecture(
            course_id=c_math.id, title="Trigonometric Identities & Ratios",
            description="Explains sine, cosine, tangent values across standard angles, and verifying trigonometric equalities.",
            video_url="https://www.youtube.com/embed/rtgYl5a1ZlY", video_type="youtube", duration=1100, order_index=2
        )
        
        db.add_all([l_c1, l_c2, l_d1, l_d2, l_m1, l_m2])
        db.flush()
        
        # Create indexed notes entries for RAG
        note_c = models.LectureNote(
            lecture_id=l_c2.id, course_id=c_prog.id, faculty_id=teacher.id,
            filename="Pointers_and_Memory_Handbook.pdf", file_url="/static/uploads/notes/Pointers_and_Memory_Handbook.pdf",
            file_type="pdf", file_size=4096, is_indexed=True, vector_ids=[f"pointers_note_0"]
        )
        note_d = models.LectureNote(
            lecture_id=l_d1.id, course_id=c_dsa.id, faculty_id=teacher.id,
            filename="LinkedLists_and_Stacks.pdf", file_url="/static/uploads/notes/LinkedLists_and_Stacks.pdf",
            file_type="pdf", file_size=8192, is_indexed=True, vector_ids=[f"dsa_note_0"]
        )
        note_m = models.LectureNote(
            lecture_id=l_m1.id, course_id=c_math.id, faculty_id=teacher.id,
            filename="Class10_QuadraticEquations_Notes.pdf", file_url="/static/uploads/notes/Class10_QuadraticEquations_Notes.pdf",
            file_type="pdf", file_size=2048, is_indexed=True, vector_ids=[f"math_note_0"]
        )
        db.add_all([note_c, note_d, note_m])
        
        print("[OK] Enrollments, lectures, and mock lecture notes seeded!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding lectures: {e}")
        return

    print("\n[5/6] Seeding live classes & placement career portal data...")
    try:
        # Schedule live sessions
        today = datetime.datetime.now()
        lc1 = models.LiveClass(
            course_id=c_prog.id, faculty_id=teacher.id,
            title="Q&A Session on pointers and reference variables",
            description="Interactive review of BTech CSE Semester 1 memory addressing pointers.",
            scheduled_at=today + datetime.timedelta(hours=2), duration_minutes=60,
            platform="zoom", meeting_url="https://zoom.us/j/123456789", meeting_id="123-456-789", status="scheduled"
        )
        lc2 = models.LiveClass(
            course_id=c_ai.id, faculty_id=teacher.id,
            title="Live Demo: Building Agentic RAG with LangChain",
            description="Hands-on build session covering ChromaDB integrations and custom AI chains.",
            scheduled_at=today + datetime.timedelta(days=1), duration_minutes=90,
            platform="meet", meeting_url="https://meet.google.com/abc-defg-hij", status="scheduled"
        )
        db.add_all([lc1, lc2])
        
        # Seed jobs/internships
        j1 = models.Internship(
            title="Backend Engineering Intern (FastAPI / Node.js)",
            company="Skill Sharp Innovations",
            description="Work closely with senior engineers to build cloud infrastructure, design secure microservice routes using FastAPI, handle databases, and package code using Docker. Strong Python or JS skills required.",
            location="Remote", type="internship", stipend="$500 / month",
            skills=["Python", "FastAPI", "MongoDB", "REST APIs", "Docker"],
            apply_url="https://skillsharp365.com/careers/backend-intern", deadline="2026-07-01", is_active=True
        )
        j2 = models.Internship(
            title="AI Engineer -- Generative AI & RAG Specialist",
            company="AlphaBrain Systems",
            description="Looking for an AI engineer to develop context-aware search pipelines using LLMs. Experience in Retrieval-Augmented Generation (RAG), vector databases (ChromaDB, Pinecone), LangChain and prompt optimization is highly desirable.",
            location="Hyderabad, India", type="job", stipend="$1,200 / month",
            skills=["LLMs", "LangChain", "Vector Embeddings", "Python", "RAG Pipeline"],
            apply_url="https://skillsharp365.com/careers/ai-engineer", deadline="2026-06-30", is_active=True
        )
        j3 = models.Internship(
            title="Security Analyst / VAPT Intern",
            company="ShieldNet Labs",
            description="Perform network security testing, application penetration testing (VAPT), vulnerability scans, and secure cloud system evaluations. Basic knowledge of OWASP Top 10 guidelines is a must.",
            location="Bengaluru, India", type="internship", stipend="$400 / month",
            skills=["Ethical Hacking", "OWASP", "VAPT", "Wireshark", "Network Security"],
            apply_url="https://skillsharp365.com/careers/security-analyst", deadline="2026-07-15", is_active=True
        )
        db.add_all([j1, j2, j3])
        
        db.commit()
        print("[OK] Live classes and Job postings seeded!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding career/live data: {e}")
        return

    print("\n[6/6] Creating JSON fallback RAG vector cache...")
    try:
        # Pre-seed text notes vector chunks in the RAG JSON cache so RAG AI tutor answers immediately
        rag_cache = {
            c_prog.id: [
                {
                    "id": "pointers_note_0",
                    "note_id": note_c.id,
                    "content": "Pointers in C are special variables that store the memory address of another variable. The dereference operator (*) is used to access or modify the value stored at that address, while the address-of operator (&) is used to retrieve the memory address of any standard variable. Pointers are essential for dynamic memory allocation, handling arrays efficiently, and passing variables by reference in function calls.",
                    "chunk_index": 0
                }
            ],
            c_dsa.id: [
                {
                    "id": "dsa_note_0",
                    "note_id": note_d.id,
                    "content": "A Stack is a linear data structure that follows the Last In, First Out (LIFO) order. Elements are added and removed from the same end, called the Top. The primary operations of a stack are push (to insert an element on top), pop (to remove and retrieve the top element), and peek/top (to view the top element without removing it). Common applications include function call stacks, undo/redo mechanisms, and validating nested parentheses.",
                    "chunk_index": 0
                }
            ],
            c_math.id: [
                {
                    "id": "math_note_0",
                    "note_id": note_m.id,
                    "content": "A Quadratic Equation is a second-degree polynomial equation of the form ax^2 + bx + c = 0, where 'a' is not equal to zero. The roots can be solved using the standard quadratic formula x = (-b ± sqrt(b^2 - 4ac)) / 2a. The term D = b^2 - 4ac is the Discriminant. If D > 0, the equation has two distinct real roots. If D = 0, it has two equal real roots. If D < 0, it has complex roots.",
                    "chunk_index": 0
                }
            ]
        }
        
        # Write to static/uploads/notes/rag_cache.json
        os.makedirs(os.path.join("static", "uploads", "notes"), exist_ok=True)
        cache_path = os.path.join("static", "uploads", "notes", "rag_cache.json")
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(rag_cache, f, indent=2, ensure_ascii=False)
            
        print("[OK] Pre-populated RAG vector cache written to static/uploads/notes/rag_cache.json!")
    except Exception as e:
        print(f"[ERROR] Error seeding RAG cache: {e}")

    db.close()
    print("\n====================================================")
    print("      [OK] DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("====================================================")

if __name__ == "__main__":
    seed_database()
