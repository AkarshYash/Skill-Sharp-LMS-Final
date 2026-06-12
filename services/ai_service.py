"""
AI Service — LangChain + Gemini + RAG
Core intelligence layer for EduAI Platform
"""
import os
import json
from typing import List, Optional
from config import settings

# ─── Gemini Setup ────────────────────────────────
def get_gemini_llm(temperature: float = 0.7):
    """Get Gemini LLM instance via LangChain"""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model       = settings.GEMINI_MODEL,
            google_api_key = settings.GEMINI_API_KEY,
            temperature = temperature,
            max_output_tokens = settings.MAX_AI_TOKENS,
            convert_system_message_to_human = True
        )
    except Exception as e:
        print(f"Gemini init error: {e}")
        return None

def get_openai_llm(temperature: float = 0.7):
    """Get OpenAI LLM instance via LangChain"""
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model       = settings.OPENAI_MODEL,
            api_key     = settings.OPENAI_API_KEY,
            temperature = temperature,
            max_tokens  = settings.MAX_AI_TOKENS
        )
    except Exception as e:
        print(f"OpenAI init error: {e}")
        return None

def get_llm(temperature: float = 0.7):
    """Get best available LLM"""
    if settings.GEMINI_API_KEY:
        llm = get_gemini_llm(temperature)
        if llm:
            return llm
    if settings.OPENAI_API_KEY:
        llm = get_openai_llm(temperature)
        if llm:
            return llm
    return None

# ─── AI Tutor (LangChain + RAG) ─────────────────
async def ai_tutor_chat(
    user_message: str,
    chat_history: List[dict],
    course_id: Optional[str] = None,
    context: Optional[str] = None
) -> str:
    """
    AI Tutor with conversation memory and RAG context.
    Uses LangChain for chaining and memory management.
    """
    llm = get_llm(temperature=0.7)
    
    if not llm:
        return mock_ai_response(user_message)
    
    # Build RAG context if course_id provided
    rag_context = ""
    if course_id:
        try:
            from services.rag_service import search_course_context
            docs = search_course_context(user_message, course_id)
            if docs:
                rag_context = "\n\n".join([d["content"] for d in docs[:3]])
        except Exception as e:
            print(f"RAG context error: {e}")
    
    # Build system prompt
    system_prompt = """You are an advanced general AI assistant. You can answer each and every question on any subject, just like ChatGPT or Gemini. You can discuss any topic and provide detailed, proper responses. You can also create any document, essay, or text content the user asks for.

CRITICAL RESTRICTION: You CANNOT create any programming code. If the user asks you to write code, write a script, or program anything, you must politely refuse and explain that you are not allowed to generate code.

Always be:
- Helpful, clear, and comprehensive
- Adaptive to the user's needs
- Strictly compliant with the no-code rule"""

    if rag_context:
        system_prompt += f"\n\nCOURSE CONTEXT (from uploaded materials):\n{rag_context}"
    
    if context:
        system_prompt += f"\n\nADDITIONAL CONTEXT:\n{context}"
    
    # Build message history for LangChain
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    messages = [SystemMessage(content=system_prompt)]
    
    # Add recent history (last 10 turns)
    for msg in chat_history[-10:]:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    
    messages.append(HumanMessage(content=user_message))
    
    try:
        response = await llm.ainvoke(messages)
        return response.content or "I couldn't generate a response. Please try again."
    except Exception as e:
        print(f"AI chat error: {e}")
        return mock_ai_response(user_message)

# ─── Quiz Generation ─────────────────────────────
async def generate_quiz_questions(
    topic: str,
    num_questions: int = 10,
    difficulty: str = "medium"
) -> List[dict]:
    """Generate quiz questions using LangChain"""
    llm = get_llm(temperature=0.6)
    
    if not llm:
        return mock_quiz_questions(topic, num_questions)
    
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert quiz creator for an educational platform.
Generate exactly {num_questions} multiple choice questions about the topic.
Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "answer": "A) Option 1",
    "explanation": "Brief explanation of why this is correct"
  }}
]
Difficulty level: {difficulty}
No extra text, just the JSON array."""),
        ("human", "Topic: {topic}")
    ])
    
    chain = prompt | llm
    
    try:
        result = await chain.ainvoke({
            "topic":         topic,
            "num_questions": num_questions,
            "difficulty":    difficulty
        })
        
        content = result.content.strip()
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        questions = json.loads(content)
        return questions[:num_questions]
    except Exception as e:
        print(f"Quiz generation error: {e}")
        return mock_quiz_questions(topic, num_questions)

# ─── Study Plan Generation ───────────────────────
async def generate_study_plan(
    goal: str,
    target_date: str,
    weekly_hours: int,
    courses: List[dict],
    student_level: str = "beginner"
) -> dict:
    """Generate AI-powered personalized study plan"""
    llm = get_llm(temperature=0.6)
    
    if not llm:
        return mock_study_plan(goal, target_date)
    
    from langchain_core.prompts import ChatPromptTemplate
    
    courses_str = "\n".join([f"- {c['title']} ({c['level']})" for c in courses[:5]])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert educational counselor creating personalized study plans.
Create a structured study plan and return ONLY valid JSON:
{{
  "title": "Plan title",
  "overview": "Brief overview",
  "milestones": [
    {{"title": "Milestone 1", "due": "YYYY-MM-DD", "completed": false}}
  ],
  "schedule": [
    {{"day": "Monday", "topic": "Topic", "duration_hours": 2, "activity": "Watch lecture + practice"}}
  ],
  "tips": ["Study tip 1", "Study tip 2", "Study tip 3"]
}}"""),
        ("human", """Goal: {goal}
Target Date: {target_date}
Weekly Hours Available: {weekly_hours}
Student Level: {student_level}
Available Courses:
{courses}

Create a realistic, detailed study plan.""")
    ])
    
    chain = prompt | llm
    
    try:
        result = await chain.ainvoke({
            "goal":          goal,
            "target_date":   target_date,
            "weekly_hours":  weekly_hours,
            "student_level": student_level,
            "courses":       courses_str
        })
        content = result.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"Study plan error: {e}")
        return mock_study_plan(goal, target_date)

# ─── Lecture Summary ─────────────────────────────
async def generate_lecture_summary(title: str, description: str, transcript: str = "") -> str:
    """Generate AI summary of a lecture"""
    llm = get_llm(temperature=0.5)
    
    if not llm:
        return f"Summary for '{title}': This lecture covers key concepts related to {description[:200]}..."
    
    from langchain_core.prompts import ChatPromptTemplate
    
    content = transcript or description
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert educational content summarizer. Create clear, structured summaries that help students understand and retain information."),
        ("human", """Lecture Title: {title}
Content: {content}

Create a comprehensive summary with:
1. **Key Concepts** (bullet points)
2. **Main Takeaways** (3-5 points)
3. **Important Terms** (if any)
4. **Quick Review Questions** (2-3 questions)

Keep it concise but comprehensive.""")
    ])
    
    chain = prompt | llm
    
    try:
        result = await chain.ainvoke({"title": title, "content": content[:3000]})
        return result.content
    except Exception as e:
        return f"Summary generation failed: {str(e)}"

# ─── Assignment Feedback ─────────────────────────
async def generate_assignment_feedback(submission_content: str) -> str:
    """Generate AI feedback on student assignment"""
    llm = get_llm(temperature=0.6)
    
    if not llm:
        return "Good effort! Review the key concepts and ensure your answer is comprehensive."
    
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a constructive academic reviewer providing helpful feedback on student assignments."),
        ("human", """Review this student submission and provide constructive feedback:

{content}

Provide:
1. **Strengths** — What the student did well
2. **Areas for Improvement** — Specific suggestions
3. **Overall Assessment** — Brief summary
4. **Grade Suggestion** — Excellent/Good/Satisfactory/Needs Work

Be encouraging and specific.""")
    ])
    
    chain = prompt | llm
    
    try:
        result = await chain.ainvoke({"content": submission_content[:2000]})
        return result.content
    except Exception as e:
        return f"Feedback generation failed: {str(e)}"

# ─── Resume Builder ──────────────────────────────
async def generate_resume(user_data: dict, courses: List[dict]) -> str:
    """Generate AI-powered resume"""
    llm = get_llm(temperature=0.6)
    
    if not llm:
        return "Resume generation requires an AI API key."
    
    from langchain_core.prompts import ChatPromptTemplate
    
    courses_str = "\n".join([f"- {c['title']} ({c['level']}) — {'Completed' if c.get('completed') else 'In Progress'}" for c in courses])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional resume writer creating ATS-friendly resumes."),
        ("human", """Create a professional resume for:
Name: {name}
Bio: {bio}
Expertise: {expertise}
LinkedIn: {linkedin}
GitHub: {github}
Courses Completed:
{courses}

Format as a clean, professional resume in markdown format.""")
    ])
    
    chain = prompt | llm
    
    try:
        result = await chain.ainvoke({
            "name":     user_data.get("name", ""),
            "bio":      user_data.get("bio", ""),
            "expertise": user_data.get("expertise", ""),
            "linkedin": user_data.get("linkedin_url", ""),
            "github":   user_data.get("github_url", ""),
            "courses":  courses_str
        })
        return result.content
    except Exception as e:
        return f"Resume generation failed: {str(e)}"

# ─── Career Recommendation ───────────────────────
async def get_career_recommendations(skills: List[str], courses: List[str], goal: str = "") -> dict:
    """Get AI career path recommendations"""
    llm = get_llm(temperature=0.7)
    
    if not llm:
        return {"paths": [], "message": "Add an AI API key for career recommendations"}
    
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a career counselor specializing in tech careers. Return JSON only."),
        ("human", """Skills: {skills}
Completed Courses: {courses}
Career Goal: {goal}

Return JSON:
{{
  "recommended_paths": [
    {{"title": "Career Path", "match": 90, "description": "...", "next_steps": ["step1", "step2"]}}
  ],
  "skill_gaps": ["skill1", "skill2"],
  "recommended_courses": ["course topic 1", "course topic 2"],
  "market_insight": "Brief market insight"
}}""")
    ])
    
    chain = prompt | llm
    
    try:
        result = await chain.ainvoke({
            "skills":  ", ".join(skills[:10]),
            "courses": ", ".join(courses[:10]),
            "goal":    goal
        })
        content = result.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        return {"error": str(e), "paths": []}

# ─── Mock Responses (fallback) ───────────────────
def mock_ai_response(message: str) -> str:
    """Intelligent rule-based fallback — answers any question without an API key."""
    msg = message.lower().strip()

    # ── Greetings ──
    greetings = ["hi", "hello", "hey", "hii", "helo", "hy", "sup", "greetings", "good morning", "good afternoon", "good evening"]
    if any(msg == g or msg.startswith(g + " ") or msg.startswith(g + "!") for g in greetings):
        return ("👋 Hello! I'm **Skill Sharp AI**, your intelligent learning assistant.\n\n"
                "I can help you with:\n"
                "• 📚 Explaining any concept (Math, Science, History, Programming, etc.)\n"
                "• ❓ Answering any factual or academic question\n"
                "• 📝 Summarizing topics and creating study notes\n"
                "• 🧮 Solving math problems step-by-step\n"
                "• 💡 Giving career and learning advice\n\n"
                "What would you like to learn or ask about today?")

    if any(w in msg for w in ["how are you", "how r u", "how do you do", "what's up", "whats up"]):
        return "I'm doing great and ready to help you learn! 🚀 What topic or question can I assist you with today?"

    if any(w in msg for w in ["who are you", "what are you", "your name", "introduce yourself"]):
        return ("I'm **Skill Sharp AI** — the built-in AI tutor for Skills Sharp 365 Innovation. 🤖\n\n"
                "I can answer questions on virtually any topic: Science, Math, History, Geography, Technology, Literature, and more. "
                "Just ask me anything!")

    if any(w in msg for w in ["thank", "thanks", "thx", "ty", "appreciate"]):
        return "You're welcome! 😊 Feel free to ask me anything else. I'm here to help you learn!"

    if any(w in msg for w in ["bye", "goodbye", "see you", "later", "cya"]):
        return "Goodbye! Keep learning and stay curious! 🌟 Come back anytime you have questions."

    # ── Math ──
    if any(w in msg for w in ["math", "calculate", "solve", "equation", "algebra", "geometry", "calculus",
                               "trigonometry", "derivative", "integral", "matrix", "probability",
                               "statistics", "factorial", "prime", "quadratic", "pythagoras"]):
        return ("📐 **Mathematics Help**\n\n"
                "I can help you with a wide range of math topics:\n"
                "• **Algebra**: Equations, polynomials, factoring, inequalities\n"
                "• **Geometry**: Areas, volumes, angles, triangles, circles\n"
                "• **Trigonometry**: sin, cos, tan, identities, unit circle\n"
                "• **Calculus**: Derivatives, integrals, limits, chain rule\n"
                "• **Statistics**: Mean, median, mode, standard deviation, probability\n"
                "• **Number Theory**: Primes, factorials, GCD, LCM\n\n"
                f"Please share the specific problem from your message: *\"{message[:80]}\"* and I'll solve it step-by-step!")

    # ── Science ──
    if any(w in msg for w in ["physics", "chemistry", "biology", "science", "atom", "molecule",
                               "force", "gravity", "energy", "electron", "photon", "cell", "dna",
                               "evolution", "element", "periodic table", "reaction", "newton", "einstein"]):
        return ("🔬 **Science Explanation**\n\n"
                f"Great question! Regarding *\"{message[:80]}\"*:\n\n"
                "Science covers a vast range of topics. Here's a structured overview:\n\n"
                "**Physics** — Studies matter, energy, forces, motion, thermodynamics, waves, and electromagnetism.\n"
                "**Chemistry** — Studies elements, compounds, chemical bonds, reactions, acids/bases, and the periodic table.\n"
                "**Biology** — Studies living organisms, cells, DNA, ecosystems, evolution, and human anatomy.\n\n"
                "💡 *Tip: Ask me a specific question like 'What is Newton\'s second law?' or 'Explain DNA replication' for a detailed answer!*")

    # ── Programming / Tech ──
    if any(w in msg for w in ["programming", "python", "java", "javascript", "html", "css", "react",
                               "database", "sql", "api", "algorithm", "data structure", "machine learning",
                               "artificial intelligence", "ai", "deep learning", "neural", "cloud",
                               "devops", "linux", "git", "docker", "kubernetes"]):
        return ("💻 **Technology & Programming**\n\n"
                f"You asked about: *\"{message[:80]}\"*\n\n"
                "Here are key areas in technology learning:\n\n"
                "• **Python** — Great for AI/ML, data science, automation, and web backends (Django/FastAPI)\n"
                "• **JavaScript** — Powers web frontends (React, Vue) and backends (Node.js)\n"
                "• **Data Structures** — Arrays, Linked Lists, Trees, Graphs, Stacks, Queues\n"
                "• **Algorithms** — Sorting (QuickSort, MergeSort), Searching (Binary Search), Dynamic Programming\n"
                "• **Databases** — SQL (MySQL, PostgreSQL), NoSQL (MongoDB), ORMs\n"
                "• **AI/ML** — Neural Networks, LangChain, RAG, Transformers, Computer Vision\n\n"
                "🎯 Ask me a specific concept like 'Explain recursion' or 'What is a REST API?' for a detailed breakdown!")

    # ── History ──
    if any(w in msg for w in ["history", "war", "revolution", "empire", "ancient", "civilization",
                               "independence", "colonial", "dynasty", "king", "queen", "medieval",
                               "world war", "cold war", "partition", "freedom fighter"]):
        return ("📜 **History**\n\n"
                f"Regarding your question: *\"{message[:80]}\"*\n\n"
                "History is the study of past human events, civilizations, and turning points.\n\n"
                "Key periods & topics:\n"
                "• **Ancient History** — Mesopotamia, Egypt, Greece, Rome, Indus Valley Civilization\n"
                "• **Medieval Period** — Feudalism, Crusades, Mughal Empire, Byzantine Empire\n"
                "• **Modern History** — Industrial Revolution, World Wars, Independence movements\n"
                "• **Indian History** — Vedic period, Maurya/Gupta empires, British Raj, 1947 Independence\n\n"
                "📌 Ask me a specific event like 'What caused World War 1?' for a detailed answer!")

    # ── Geography ──
    if any(w in msg for w in ["geography", "capital", "country", "continent", "ocean", "mountain",
                               "river", "climate", "population", "map", "latitude", "longitude"]):
        return ("🌍 **Geography**\n\n"
                f"Regarding: *\"{message[:80]}\"*\n\n"
                "Geography covers the Earth's features, peoples, and environments:\n\n"
                "• **Physical Geography** — Mountains, rivers, oceans, climate zones, tectonic plates\n"
                "• **Human Geography** — Population, culture, cities, trade routes\n"
                "• **Countries & Capitals** — There are 195 countries in the world\n"
                "• **Notable Facts**: Largest country = Russia | Smallest = Vatican City | Most populous = India\n\n"
                "Ask me specific questions like 'What is the capital of France?' for precise answers!")

    # ── Economics / Business ──
    if any(w in msg for w in ["economics", "gdp", "inflation", "market", "business", "startup",
                               "finance", "investment", "stock", "trade", "demand", "supply",
                               "entrepreneurship", "budget", "recession"]):
        return ("📊 **Economics & Business**\n\n"
                f"Your question: *\"{message[:80]}\"*\n\n"
                "Key economic concepts:\n\n"
                "• **Microeconomics** — Supply & demand, market equilibrium, consumer behavior\n"
                "• **Macroeconomics** — GDP, inflation, unemployment, monetary policy\n"
                "• **Business** — Entrepreneurship, marketing, operations, finance\n"
                "• **Finance** — Stocks, bonds, mutual funds, interest rates, risk management\n\n"
                "💡 *Example: 'What is GDP?' or 'Explain inflation' — ask away!*")

    # ── English / Literature ──
    if any(w in msg for w in ["english", "grammar", "essay", "literature", "poem", "novel",
                               "shakespeare", "writing", "vocabulary", "tense", "synonym", "antonym"]):
        return ("📖 **English & Literature**\n\n"
                f"For your query: *\"{message[:80]}\"*\n\n"
                "I can help with:\n"
                "• **Grammar** — Tenses, articles, prepositions, subject-verb agreement\n"
                "• **Writing** — Essays, paragraphs, formal/informal letters, reports\n"
                "• **Literature** — Shakespeare, Dickens, poetry analysis, story themes\n"
                "• **Vocabulary** — Synonyms, antonyms, idioms, phrasal verbs\n\n"
                "Ask me to 'explain past perfect tense' or 'summarize Romeo and Juliet' for detailed help!")

    # ── Career / Jobs ──
    if any(w in msg for w in ["career", "job", "resume", "interview", "salary", "internship",
                               "placement", "skills", "linkedin", "portfolio", "fresher"]):
        return ("💼 **Career Guidance**\n\n"
                f"Regarding: *\"{message[:80]}\"*\n\n"
                "Career tips for students and freshers:\n\n"
                "1. **Build skills** — Focus on in-demand skills (Python, AI, Cloud, Data Analysis)\n"
                "2. **Create a strong resume** — Highlight projects, internships, and certifications\n"
                "3. **Prepare for interviews** — Practice DSA, system design, and HR questions\n"
                "4. **Network** — Connect on LinkedIn, attend tech events and hackathons\n"
                "5. **Apply consistently** — Use platforms like LinkedIn, Naukri, Internshala, AngelList\n\n"
                "🎯 Use the Career Portal and AI Interview Prep sections for hands-on practice!")

    # ── Generic intelligent fallback for anything else ──
    topic = message[:60].strip()
    return (f"🤖 **Skill Sharp AI — Response**\n\n"
            f"You asked: *\"{topic}{'...' if len(message) > 60 else ''}\"*\n\n"
            "Great question! Here's how I can help you explore this topic:\n\n"
            "📌 **To get the most accurate, detailed answer:**\n"
            "• Be specific — e.g., instead of 'explain AI', ask 'What is supervised learning in machine learning?'\n"
            "• Ask follow-up questions to dive deeper into any concept\n"
            "• Request examples, comparisons, or step-by-step explanations\n\n"
            "📚 **Related learning resources on Skills Sharp 365:**\n"
            "• Browse courses in the **Courses** section\n"
            "• Use **AI Tutor** for in-depth concept explanations\n"
            "• Try **Quizzes** to test your understanding\n\n"
            "💡 *Add a Gemini or OpenAI API key in the `.env` file to unlock full AI-powered answers for any question!*")

def mock_quiz_questions(topic: str, n: int) -> List[dict]:
    return [
        {
            "question":    f"What is the main concept of {topic}? (Question {i+1})",
            "options":     ["A) First concept", "B) Second concept", "C) Third concept", "D) Fourth concept"],
            "answer":      "A) First concept",
            "explanation": f"This relates to the fundamental aspects of {topic}."
        }
        for i in range(min(n, 5))
    ]

def mock_study_plan(goal: str, target_date: str) -> dict:
    return {
        "title":     f"Study Plan: {goal[:50]}",
        "overview":  f"A structured plan to achieve your goal by {target_date}",
        "milestones": [
            {"title": "Foundation",         "due": "2026-06-30", "completed": False},
            {"title": "Core Concepts",      "due": "2026-07-31", "completed": False},
            {"title": "Advanced Topics",    "due": "2026-08-31", "completed": False},
            {"title": "Final Review",       "due": target_date,  "completed": False},
        ],
        "schedule": [
            {"day": "Monday",    "topic": "Theory & Concepts",      "duration_hours": 2, "activity": "Watch lectures"},
            {"day": "Wednesday", "topic": "Practice & Exercises",   "duration_hours": 2, "activity": "Solve problems"},
            {"day": "Friday",    "topic": "Review & Quizzes",       "duration_hours": 1, "activity": "Take quizzes"},
            {"day": "Saturday",  "topic": "Projects & Application", "duration_hours": 3, "activity": "Build projects"},
        ],
        "tips": [
            "Study consistently every day for at least 30 minutes",
            "Take breaks using the Pomodoro technique (25 min study, 5 min break)",
            "Review your notes within 24 hours of each lecture",
            "Practice with real-world projects",
            "Join study groups and discussion forums"
        ]
    }
