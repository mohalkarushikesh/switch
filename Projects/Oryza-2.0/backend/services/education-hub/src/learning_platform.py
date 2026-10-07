"""
Enhanced Educational Platform - Interactive courses, certifications, and gamified learning
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

class CourseLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ContentType(Enum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"
    SIMULATION = "simulation"
    CASE_STUDY = "case_study"

class LearningPlatform:
    """
    Comprehensive educational platform for financial literacy and trading education
    """
    
    def __init__(self):
        self.courses = {}
        self.enrollments = {}
        self.progress = {}
        self.certificates = {}
        self.quiz_results = {}
        self.learning_paths = {}
        self.achievements = {}
        
        # Initialize course catalog
        self._initialize_course_catalog()
        
        # Gamification elements
        self.badges = {
            "first_course": {"name": "First Step", "description": "Complete your first course"},
            "quiz_master": {"name": "Quiz Master", "description": "Score 90%+ on 10 quizzes"},
            "speed_learner": {"name": "Speed Learner", "description": "Complete a course in under a week"},
            "knowledge_seeker": {"name": "Knowledge Seeker", "description": "Enroll in 10 courses"},
            "certified_trader": {"name": "Certified Trader", "description": "Earn trading certification"},
            "investment_guru": {"name": "Investment Guru", "description": "Complete all investment courses"}
        }
    
    def _initialize_course_catalog(self):
        """Initialize course catalog with comprehensive content"""
        
        self.courses = {
            "basics_101": {
                "course_id": "basics_101",
                "title": "Introduction to Investing",
                "description": "Learn the fundamentals of investing and wealth creation",
                "level": CourseLevel.BEGINNER.value,
                "duration": "4 weeks",
                "modules": [
                    {
                        "module_id": "m1",
                        "title": "What is Investing?",
                        "lessons": [
                            {"title": "Why Invest?", "type": ContentType.VIDEO.value, "duration": "15 min"},
                            {"title": "Types of Investments", "type": ContentType.TEXT.value, "duration": "20 min"},
                            {"title": "Risk vs Return", "type": ContentType.INTERACTIVE.value, "duration": "25 min"},
                            {"title": "Module Quiz", "type": ContentType.QUIZ.value, "questions": 10}
                        ]
                    },
                    {
                        "module_id": "m2",
                        "title": "Stock Market Basics",
                        "lessons": [
                            {"title": "What are Stocks?", "type": ContentType.VIDEO.value, "duration": "20 min"},
                            {"title": "How Stock Markets Work", "type": ContentType.SIMULATION.value, "duration": "30 min"},
                            {"title": "Reading Stock Quotes", "type": ContentType.INTERACTIVE.value, "duration": "15 min"}
                        ]
                    }
                ],
                "prerequisites": [],
                "certification": True,
                "price": 0,  # Free course
                "rating": 4.8,
                "enrolled": 15420
            },
            
            "technical_analysis": {
                "course_id": "technical_analysis",
                "title": "Mastering Technical Analysis",
                "description": "Learn to read charts and predict market movements",
                "level": CourseLevel.INTERMEDIATE.value,
                "duration": "6 weeks",
                "modules": [
                    {
                        "module_id": "ta1",
                        "title": "Chart Patterns",
                        "lessons": [
                            {"title": "Candlestick Patterns", "type": ContentType.VIDEO.value, "duration": "30 min"},
                            {"title": "Support and Resistance", "type": ContentType.INTERACTIVE.value, "duration": "25 min"},
                            {"title": "Trend Analysis", "type": ContentType.SIMULATION.value, "duration": "40 min"}
                        ]
                    },
                    {
                        "module_id": "ta2",
                        "title": "Technical Indicators",
                        "lessons": [
                            {"title": "Moving Averages", "type": ContentType.VIDEO.value, "duration": "25 min"},
                            {"title": "RSI and MACD", "type": ContentType.INTERACTIVE.value, "duration": "30 min"},
                            {"title": "Bollinger Bands", "type": ContentType.TEXT.value, "duration": "20 min"}
                        ]
                    }
                ],
                "prerequisites": ["basics_101"],
                "certification": True,
                "price": 4999,
                "rating": 4.6,
                "enrolled": 8234
            },
            
            "ai_trading": {
                "course_id": "ai_trading",
                "title": "AI-Powered Trading Strategies",
                "description": "Leverage AI and machine learning for trading",
                "level": CourseLevel.ADVANCED.value,
                "duration": "8 weeks",
                "modules": [
                    {
                        "module_id": "ai1",
                        "title": "Introduction to AI in Finance",
                        "lessons": [
                            {"title": "ML Fundamentals", "type": ContentType.VIDEO.value, "duration": "45 min"},
                            {"title": "AI Trading Algorithms", "type": ContentType.TEXT.value, "duration": "30 min"},
                            {"title": "Building Your First Bot", "type": ContentType.INTERACTIVE.value, "duration": "60 min"}
                        ]
                    }
                ],
                "prerequisites": ["technical_analysis"],
                "certification": True,
                "price": 9999,
                "rating": 4.9,
                "enrolled": 3456
            },
            
            "esg_investing": {
                "course_id": "esg_investing",
                "title": "Sustainable & ESG Investing",
                "description": "Invest with impact - Environmental, Social, and Governance principles",
                "level": CourseLevel.INTERMEDIATE.value,
                "duration": "4 weeks",
                "modules": [
                    {
                        "module_id": "esg1",
                        "title": "Understanding ESG",
                        "lessons": [
                            {"title": "What is ESG?", "type": ContentType.VIDEO.value, "duration": "20 min"},
                            {"title": "ESG Scoring Methods", "type": ContentType.TEXT.value, "duration": "25 min"},
                            {"title": "Impact Measurement", "type": ContentType.CASE_STUDY.value, "duration": "35 min"}
                        ]
                    }
                ],
                "prerequisites": ["basics_101"],
                "certification": True,
                "price": 2999,
                "rating": 4.7,
                "enrolled": 5678
            }
        }
        
        # Define learning paths
        self.learning_paths = {
            "beginner_investor": {
                "name": "Beginner Investor Path",
                "description": "Start your investment journey from scratch",
                "courses": ["basics_101", "esg_investing"],
                "duration": "8 weeks",
                "difficulty": "beginner"
            },
            "active_trader": {
                "name": "Active Trader Path",
                "description": "Become a skilled active trader",
                "courses": ["basics_101", "technical_analysis", "ai_trading"],
                "duration": "18 weeks",
                "difficulty": "advanced"
            },
            "sustainable_investor": {
                "name": "Sustainable Investor Path",
                "description": "Focus on sustainable and ethical investing",
                "courses": ["basics_101", "esg_investing"],
                "duration": "8 weeks",
                "difficulty": "intermediate"
            }
        }
    
    async def enroll_in_course(
        self,
        user_id: str,
        course_id: str,
        payment_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enroll user in a course"""
        
        if course_id not in self.courses:
            return {"error": "Course not found"}
        
        course = self.courses[course_id]
        
        # Check prerequisites
        if course["prerequisites"]:
            completed_courses = await self._get_completed_courses(user_id)
            for prereq in course["prerequisites"]:
                if prereq not in completed_courses:
                    prereq_course = self.courses.get(prereq, {})
                    return {
                        "error": f"Prerequisite required: {prereq_course.get('title', prereq)}"
                    }
        
        # Process payment if required
        if course["price"] > 0:
            if not payment_info:
                return {"error": "Payment required"}
            
            payment_result = await self._process_payment(user_id, course["price"], payment_info)
            if not payment_result["success"]:
                return {"error": "Payment failed"}
        
        # Create enrollment
        enrollment_id = f"enroll_{uuid.uuid4().hex[:12]}"
        enrollment = {
            "enrollment_id": enrollment_id,
            "user_id": user_id,
            "course_id": course_id,
            "enrolled_at": datetime.now().isoformat(),
            "status": "active",
            "progress": 0,
            "completed_modules": [],
            "completed_lessons": [],
            "current_module": 0,
            "current_lesson": 0
        }
        
        if user_id not in self.enrollments:
            self.enrollments[user_id] = []
        
        self.enrollments[user_id].append(enrollment)
        
        # Initialize progress tracking
        progress_key = f"{user_id}:{course_id}"
        self.progress[progress_key] = {
            "overall_progress": 0,
            "module_progress": {},
            "quiz_scores": {},
            "time_spent": 0,
            "last_accessed": datetime.now().isoformat()
        }
        
        # Update course enrollment count
        course["enrolled"] += 1
        
        # Check for achievements
        await self._check_achievements(user_id, "enrollment")
        
        return {
            "enrollment": enrollment,
            "course": course,
            "message": f"Successfully enrolled in {course['title']}"
        }
    
    async def get_lesson_content(
        self,
        user_id: str,
        course_id: str,
        module_id: str,
        lesson_index: int
    ) -> Dict[str, Any]:
        """Get lesson content with progress tracking"""
        
        # Verify enrollment
        if not await self._is_enrolled(user_id, course_id):
            return {"error": "Not enrolled in this course"}
        
        course = self.courses[course_id]
        module = next((m for m in course["modules"] if m["module_id"] == module_id), None)
        
        if not module:
            return {"error": "Module not found"}
        
        if lesson_index >= len(module["lessons"]):
            return {"error": "Lesson not found"}
        
        lesson = module["lessons"][lesson_index]
        
        # Generate content based on type
        content = await self._generate_lesson_content(lesson, course_id, module_id)
        
        # Update progress
        await self._update_progress(user_id, course_id, module_id, lesson_index)
        
        return {
            "lesson": lesson,
            "content": content,
            "progress": await self._get_course_progress(user_id, course_id)
        }
    
    async def _generate_lesson_content(
        self,
        lesson: Dict[str, Any],
        course_id: str,
        module_id: str
    ) -> Dict[str, Any]:
        """Generate lesson content based on type"""
        
        if lesson["type"] == ContentType.VIDEO.value:
            return {
                "type": "video",
                "url": f"https://cdn.oryza.ai/courses/{course_id}/{module_id}/{lesson['title']}.mp4",
                "transcript": "Video transcript available...",
                "downloadable": True
            }
        
        elif lesson["type"] == ContentType.TEXT.value:
            return {
                "type": "text",
                "content": self._generate_text_content(lesson["title"]),
                "images": [
                    f"https://cdn.oryza.ai/courses/{course_id}/img1.png",
                    f"https://cdn.oryza.ai/courses/{course_id}/img2.png"
                ],
                "references": ["Book 1", "Article 2"]
            }
        
        elif lesson["type"] == ContentType.QUIZ.value:
            return {
                "type": "quiz",
                "questions": self._generate_quiz_questions(lesson.get("questions", 10)),
                "time_limit": 30,  # minutes
                "passing_score": 70
            }
        
        elif lesson["type"] == ContentType.INTERACTIVE.value:
            return {
                "type": "interactive",
                "simulation_url": f"https://app.oryza.ai/simulations/{course_id}/{module_id}",
                "instructions": "Interactive trading simulation instructions..."
            }
        
        elif lesson["type"] == ContentType.SIMULATION.value:
            return {
                "type": "simulation",
                "scenario": self._generate_simulation_scenario(),
                "starting_capital": 100000,
                "objectives": ["Achieve 10% return", "Maintain risk below 5%"]
            }
        
        elif lesson["type"] == ContentType.CASE_STUDY.value:
            return {
                "type": "case_study",
                "title": "Real-world ESG Investment Case",
                "background": "Company X faced environmental challenges...",
                "questions": ["What would you do?", "Analyze the impact"],
                "resources": ["Financial statements", "ESG reports"]
            }
        
        return {"type": "unknown", "content": "Content not available"}
    
    def _generate_text_content(self, title: str) -> str:
        """Generate text content for lessons"""
        # In production, this would fetch from CMS/database
        content_map = {
            "Why Invest?": """
                # Why Should You Invest?
                
                Investing is the process of putting your money to work to potentially earn more money over time.
                
                ## Key Reasons to Invest:
                
                1. **Beat Inflation**: Money sitting in a savings account loses purchasing power over time
                2. **Grow Wealth**: Compound interest can significantly grow your money
                3. **Financial Goals**: Achieve major life goals like retirement, education, or buying a home
                4. **Passive Income**: Generate income without active work
                
                ## The Power of Compounding
                
                Einstein called compound interest the "eighth wonder of the world". Here's why:
                - ₹10,000 invested at 12% annual return becomes ₹31,000 in 10 years
                - The same amount becomes ₹96,000 in 20 years
                - And an amazing ₹299,000 in 30 years!
                
                Start early, stay consistent, and let time work its magic.
            """,
            "default": "Comprehensive lesson content about " + title
        }
        
        return content_map.get(title, content_map["default"])
    
    def _generate_quiz_questions(self, num_questions: int) -> List[Dict[str, Any]]:
        """Generate quiz questions"""
        
        # Sample questions - in production, these would be from a question bank
        questions = [
            {
                "question": "What is the primary purpose of investing?",
                "options": [
                    "To keep money safe",
                    "To grow wealth over time",
                    "To avoid taxes",
                    "To impress friends"
                ],
                "correct": 1,
                "explanation": "Investing helps grow wealth by putting money to work in assets that appreciate over time."
            },
            {
                "question": "What is compound interest?",
                "options": [
                    "Interest paid by companies",
                    "Interest earned on interest",
                    "Fixed interest rate",
                    "Government interest"
                ],
                "correct": 1,
                "explanation": "Compound interest is earning interest on both principal and previously earned interest."
            },
            {
                "question": "Which typically has higher risk and return?",
                "options": [
                    "Savings account",
                    "Government bonds",
                    "Stocks",
                    "Fixed deposits"
                ],
                "correct": 2,
                "explanation": "Stocks generally offer higher potential returns but come with higher risk."
            }
        ]
        
        # Add more questions as needed
        while len(questions) < num_questions:
            questions.append(questions[len(questions) % 3])  # Cycle through questions
        
        return questions[:num_questions]
    
    def _generate_simulation_scenario(self) -> Dict[str, Any]:
        """Generate trading simulation scenario"""
        
        scenarios = [
            {
                "name": "Bull Market Rally",
                "description": "Markets are trending up. Build a growth portfolio.",
                "market_conditions": {
                    "trend": "bullish",
                    "volatility": "low",
                    "economic_indicators": "positive"
                },
                "available_stocks": ["RELIANCE", "TCS", "HDFC", "INFY"],
                "events": [
                    {"day": 5, "event": "Positive earnings report", "impact": "positive"},
                    {"day": 10, "event": "Fed announcement", "impact": "neutral"}
                ]
            },
            {
                "name": "Market Correction",
                "description": "Markets are volatile. Protect your portfolio.",
                "market_conditions": {
                    "trend": "bearish",
                    "volatility": "high",
                    "economic_indicators": "mixed"
                },
                "available_stocks": ["GOLD", "HDFC", "ITC", "PHARMA"],
                "events": [
                    {"day": 3, "event": "Global selloff", "impact": "negative"},
                    {"day": 8, "event": "Government stimulus", "impact": "positive"}
                ]
            }
        ]
        
        import random
        return random.choice(scenarios)
    
    async def submit_quiz(
        self,
        user_id: str,
        course_id: str,
        module_id: str,
        answers: List[int]
    ) -> Dict[str, Any]:
        """Submit quiz answers and get results"""
        
        # Get quiz questions
        course = self.courses[course_id]
        module = next((m for m in course["modules"] if m["module_id"] == module_id), None)
        quiz_lesson = next((l for l in module["lessons"] if l["type"] == ContentType.QUIZ.value), None)
        
        if not quiz_lesson:
            return {"error": "Quiz not found"}
        
        questions = self._generate_quiz_questions(quiz_lesson.get("questions", 10))
        
        # Calculate score
        correct_answers = 0
        results = []
        
        for i, answer in enumerate(answers):
            if i < len(questions):
                is_correct = answer == questions[i]["correct"]
                if is_correct:
                    correct_answers += 1
                
                results.append({
                    "question": questions[i]["question"],
                    "your_answer": answer,
                    "correct_answer": questions[i]["correct"],
                    "is_correct": is_correct,
                    "explanation": questions[i]["explanation"]
                })
        
        score = (correct_answers / len(questions)) * 100
        passed = score >= 70  # 70% passing score
        
        # Save quiz result
        quiz_key = f"{user_id}:{course_id}:{module_id}"
        if quiz_key not in self.quiz_results:
            self.quiz_results[quiz_key] = []
        
        quiz_result = {
            "attempt": len(self.quiz_results[quiz_key]) + 1,
            "score": score,
            "passed": passed,
            "answers": answers,
            "submitted_at": datetime.now().isoformat()
        }
        
        self.quiz_results[quiz_key].append(quiz_result)
        
        # Update progress if passed
        if passed:
            progress_key = f"{user_id}:{course_id}"
            if progress_key in self.progress:
                self.progress[progress_key]["quiz_scores"][module_id] = score
        
        # Check achievements
        await self._check_achievements(user_id, "quiz", score)
        
        return {
            "score": score,
            "passed": passed,
            "results": results,
            "certificate_eligible": await self._check_certificate_eligibility(user_id, course_id)
        }
    
    async def get_certificate(
        self,
        user_id: str,
        course_id: str
    ) -> Dict[str, Any]:
        """Generate course completion certificate"""
        
        if not await self._check_certificate_eligibility(user_id, course_id):
            return {"error": "Not eligible for certificate yet"}
        
        course = self.courses[course_id]
        
        # Generate certificate
        certificate_id = f"cert_{uuid.uuid4().hex[:8]}"
        certificate = {
            "certificate_id": certificate_id,
            "user_id": user_id,
            "course_id": course_id,
            "course_title": course["title"],
            "issue_date": datetime.now().isoformat(),
            "verification_url": f"https://oryza.ai/verify/{certificate_id}",
            "skills": self._get_course_skills(course_id),
            "grade": await self._calculate_final_grade(user_id, course_id)
        }
        
        # Store certificate
        if user_id not in self.certificates:
            self.certificates[user_id] = []
        
        self.certificates[user_id].append(certificate)
        
        # Award certification badge
        await self._check_achievements(user_id, "certificate")
        
        return {
            "certificate": certificate,
            "download_url": f"https://cdn.oryza.ai/certificates/{certificate_id}.pdf",
            "share_url": f"https://oryza.ai/share/certificate/{certificate_id}"
        }
    
    async def get_learning_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning dashboard for user"""
        
        # Get enrollments
        user_enrollments = self.enrollments.get(user_id, [])
        
        # Calculate stats
        total_courses = len(user_enrollments)
        completed_courses = len([e for e in user_enrollments if e.get("progress", 0) == 100])
        total_time_spent = sum(
            self.progress.get(f"{user_id}:{e['course_id']}", {}).get("time_spent", 0)
            for e in user_enrollments
        )
        
        # Get current courses
        current_courses = []
        for enrollment in user_enrollments:
            if enrollment["status"] == "active" and enrollment.get("progress", 0) < 100:
                course = self.courses[enrollment["course_id"]]
                progress = await self._get_course_progress(user_id, enrollment["course_id"])
                
                current_courses.append({
                    "course": course,
                    "progress": progress,
                    "next_lesson": await self._get_next_lesson(user_id, enrollment["course_id"])
                })
        
        # Get achievements
        user_achievements = self.achievements.get(user_id, [])
        
        # Get certificates
        user_certificates = self.certificates.get(user_id, [])
        
        # Get recommended courses
        recommendations = await self._get_course_recommendations(user_id)
        
        return {
            "statistics": {
                "total_courses": total_courses,
                "completed_courses": completed_courses,
                "total_time_spent": total_time_spent,
                "certificates_earned": len(user_certificates),
                "achievements_unlocked": len(user_achievements)
            },
            "current_courses": current_courses,
            "achievements": user_achievements,
            "certificates": user_certificates,
            "recommendations": recommendations,
            "learning_streak": await self._calculate_learning_streak(user_id)
        }
    
    async def _is_enrolled(self, user_id: str, course_id: str) -> bool:
        """Check if user is enrolled in course"""
        user_enrollments = self.enrollments.get(user_id, [])
        return any(e["course_id"] == course_id for e in user_enrollments)
    
    async def _get_completed_courses(self, user_id: str) -> List[str]:
        """Get list of completed course IDs"""
        user_enrollments = self.enrollments.get(user_id, [])
        return [
            e["course_id"] for e in user_enrollments
            if e.get("progress", 0) == 100
        ]
    
    async def _update_progress(
        self,
        user_id: str,
        course_id: str,
        module_id: str,
        lesson_index: int
    ):
        """Update user's progress in course"""
        progress_key = f"{user_id}:{course_id}"
        
        if progress_key not in self.progress:
            self.progress[progress_key] = {
                "overall_progress": 0,
                "module_progress": {},
                "completed_lessons": [],
                "time_spent": 0
            }
        
        # Mark lesson as completed
        lesson_key = f"{module_id}:{lesson_index}"
        if lesson_key not in self.progress[progress_key]["completed_lessons"]:
            self.progress[progress_key]["completed_lessons"].append(lesson_key)
        
        # Update overall progress
        course = self.courses[course_id]
        total_lessons = sum(len(m["lessons"]) for m in course["modules"])
        completed_lessons = len(self.progress[progress_key]["completed_lessons"])
        
        self.progress[progress_key]["overall_progress"] = (completed_lessons / total_lessons) * 100
        
        # Update enrollment progress
        for enrollment in self.enrollments.get(user_id, []):
            if enrollment["course_id"] == course_id:
                enrollment["progress"] = self.progress[progress_key]["overall_progress"]
                enrollment["current_module"] = module_id
                enrollment["current_lesson"] = lesson_index
    
    async def _get_course_progress(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """Get detailed course progress"""
        progress_key = f"{user_id}:{course_id}"
        return self.progress.get(progress_key, {"overall_progress": 0})
    
    async def _check_certificate_eligibility(self, user_id: str, course_id: str) -> bool:
        """Check if user is eligible for certificate"""
        progress = await self._get_course_progress(user_id, course_id)
        
        # Check overall completion
        if progress.get("overall_progress", 0) < 100:
            return False
        
        # Check quiz scores
        course = self.courses[course_id]
        for module in course["modules"]:
            quiz_score = progress.get("quiz_scores", {}).get(module["module_id"], 0)
            if quiz_score < 70:  # 70% minimum
                return False
        
        return True
    
    async def _calculate_final_grade(self, user_id: str, course_id: str) -> str:
        """Calculate final grade for course"""
        progress = await self._get_course_progress(user_id, course_id)
        quiz_scores = progress.get("quiz_scores", {})
        
        if not quiz_scores:
            return "Pass"
        
        avg_score = sum(quiz_scores.values()) / len(quiz_scores)
        
        if avg_score >= 90:
            return "A+"
        elif avg_score >= 80:
            return "A"
        elif avg_score >= 70:
            return "B"
        else:
            return "Pass"
    
    def _get_course_skills(self, course_id: str) -> List[str]:
        """Get skills learned from course"""
        skills_map = {
            "basics_101": ["Investment Fundamentals", "Risk Management", "Portfolio Basics"],
            "technical_analysis": ["Chart Reading", "Technical Indicators", "Trading Strategies"],
            "ai_trading": ["Algorithmic Trading", "Machine Learning", "Quantitative Analysis"],
            "esg_investing": ["ESG Analysis", "Impact Investing", "Sustainable Finance"]
        }
        
        return skills_map.get(course_id, ["Financial Literacy"])
    
    async def _get_next_lesson(self, user_id: str, course_id: str) -> Optional[Dict[str, Any]]:
        """Get next lesson for user"""
        for enrollment in self.enrollments.get(user_id, []):
            if enrollment["course_id"] == course_id:
                course = self.courses[course_id]
                current_module = enrollment.get("current_module", 0)
                current_lesson = enrollment.get("current_lesson", 0)
                
                # Find current module
                if isinstance(current_module, str):
                    module_idx = next(
                        (i for i, m in enumerate(course["modules"]) if m["module_id"] == current_module),
                        0
                    )
                else:
                    module_idx = current_module
                
                if module_idx < len(course["modules"]):
                    module = course["modules"][module_idx]
                    if current_lesson < len(module["lessons"]) - 1:
                        # Next lesson in same module
                        return {
                            "module": module["title"],
                            "lesson": module["lessons"][current_lesson + 1]["title"]
                        }
                    elif module_idx < len(course["modules"]) - 1:
                        # First lesson of next module
                        next_module = course["modules"][module_idx + 1]
                        return {
                            "module": next_module["title"],
                            "lesson": next_module["lessons"][0]["title"]
                        }
        
        return None
    
    async def _get_course_recommendations(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get personalized course recommendations"""
        completed = await self._get_completed_courses(user_id)
        enrolled = [e["course_id"] for e in self.enrollments.get(user_id, [])]
        
        recommendations = []
        
        # Recommend based on prerequisites met
        for course_id, course in self.courses.items():
            if course_id in enrolled:
                continue
            
            # Check if prerequisites are met
            prereqs_met = all(p in completed for p in course["prerequisites"])
            
            if prereqs_met or not course["prerequisites"]:
                score = course["rating"] * course["enrolled"] / 1000  # Popularity score
                
                recommendations.append({
                    "course": course,
                    "reason": "Based on your completed courses" if prereqs_met else "Popular course",
                    "match_score": score
                })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        return recommendations[:limit]
    
    async def _check_achievements(self, user_id: str, action: str, data: Any = None):
        """Check and award achievements"""
        if user_id not in self.achievements:
            self.achievements[user_id] = []
        
        user_achievements = self.achievements[user_id]
        
        if action == "enrollment":
            # First course badge
            if len(self.enrollments.get(user_id, [])) == 1:
                if "first_course" not in user_achievements:
                    user_achievements.append({
                        "badge": "first_course",
                        "earned_at": datetime.now().isoformat()
                    })
            
            # Knowledge seeker badge
            if len(self.enrollments.get(user_id, [])) >= 10:
                if not any(a["badge"] == "knowledge_seeker" for a in user_achievements):
                    user_achievements.append({
                        "badge": "knowledge_seeker",
                        "earned_at": datetime.now().isoformat()
                    })
        
        elif action == "quiz" and data:
            # Quiz master badge
            high_score_quizzes = sum(
                1 for results in self.quiz_results.values()
                if any(r["score"] >= 90 for r in results)
            )
            
            if high_score_quizzes >= 10:
                if not any(a["badge"] == "quiz_master" for a in user_achievements):
                    user_achievements.append({
                        "badge": "quiz_master",
                        "earned_at": datetime.now().isoformat()
                    })
        
        elif action == "certificate":
            # Check for specific certification badges
            trading_courses = ["technical_analysis", "ai_trading"]
            completed_trading = [
                c for c in await self._get_completed_courses(user_id)
                if c in trading_courses
            ]
            
            if len(completed_trading) >= 2:
                if not any(a["badge"] == "certified_trader" for a in user_achievements):
                    user_achievements.append({
                        "badge": "certified_trader",
                        "earned_at": datetime.now().isoformat()
                    })
    
    async def _calculate_learning_streak(self, user_id: str) -> int:
        """Calculate consecutive days of learning"""
        # In production, this would track actual daily activity
        import random
        return random.randint(1, 30)
    
    async def _process_payment(
        self,
        user_id: str,
        amount: float,
        payment_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment for paid courses"""
        # Simulate payment processing
        import random
        
        if random.random() > 0.05:  # 95% success rate
            return {
                "success": True,
                "transaction_id": f"txn_{uuid.uuid4().hex[:16]}",
                "amount": amount
            }
        else:
            return {
                "success": False,
                "message": "Payment declined"
            } 