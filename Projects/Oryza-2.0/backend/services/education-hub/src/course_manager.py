"""
Course Manager - Manages courses, modules, and lessons
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import json

from .models import (
    Course, Module, Lesson, SkillLevel, LessonType
)


class CourseManager:
    """
    Manages educational courses and content
    """
    
    def __init__(self):
        self.logger = logging.getLogger("course_manager")
        self.courses = {}  # course_id -> Course
        self.modules = {}  # module_id -> Module
        self.lessons = {}  # lesson_id -> Lesson
        self.enrollments = {}  # user_id -> Set[course_id]
        self.user_progress = {}  # (user_id, course_id) -> progress_data
        
    async def initialize(self):
        """Initialize course manager"""
        self.logger.info("Initializing Course Manager")
        
        # In production:
        # - Load courses from database
        # - Initialize content delivery network
        # - Set up video streaming
        
        # Create sample courses
        await self._create_sample_courses()
        
    async def _create_sample_courses(self):
        """Create sample courses for testing"""
        # Beginner Course
        beginner_course = Course(
            title="Introduction to Investing",
            subtitle="Start your investment journey with confidence",
            description="Learn the fundamentals of investing, from basic concepts to building your first portfolio. Perfect for absolute beginners.",
            category="Investing Basics",
            tags=["beginner", "investing", "stocks", "bonds", "portfolio"],
            skill_level=SkillLevel.BEGINNER,
            duration_hours=10.5,
            instructor_name="Dr. Sarah Chen",
            instructor_bio="PhD in Finance, 15+ years teaching experience",
            module_count=5,
            lesson_count=25,
            quiz_count=5,
            enrolled_count=1234,
            rating=4.8,
            review_count=567,
            learning_outcomes=[
                "Understand basic investment concepts and terminology",
                "Learn about different asset classes",
                "Build a diversified portfolio",
                "Manage investment risks",
                "Set realistic investment goals"
            ],
            is_featured=True
        )
        self.courses[beginner_course.course_id] = beginner_course
        
        # Create modules for beginner course
        modules = [
            {
                "title": "Investment Fundamentals",
                "description": "Core concepts every investor should know",
                "lessons": [
                    ("What is Investing?", LessonType.VIDEO, 15),
                    ("Risk vs Return", LessonType.INTERACTIVE, 20),
                    ("Time Value of Money", LessonType.ARTICLE, 10),
                    ("Compound Interest Magic", LessonType.SIMULATION, 25),
                    ("Module Quiz", LessonType.INTERACTIVE, 15)
                ]
            },
            {
                "title": "Understanding Asset Classes",
                "description": "Explore stocks, bonds, and more",
                "lessons": [
                    ("Introduction to Stocks", LessonType.VIDEO, 20),
                    ("Understanding Bonds", LessonType.VIDEO, 18),
                    ("Real Estate Basics", LessonType.ARTICLE, 15),
                    ("Commodities & Alternatives", LessonType.VIDEO, 22),
                    ("Asset Class Comparison", LessonType.CASE_STUDY, 30)
                ]
            }
        ]
        
        for i, module_data in enumerate(modules):
            module = Module(
                course_id=beginner_course.course_id,
                title=module_data["title"],
                description=module_data["description"],
                order=i + 1,
                lesson_count=len(module_data["lessons"]),
                estimated_time_minutes=sum(l[2] for l in module_data["lessons"])
            )
            self.modules[module.module_id] = module
            
            # Create lessons
            for j, (lesson_title, lesson_type, duration) in enumerate(module_data["lessons"]):
                lesson = Lesson(
                    module_id=module.module_id,
                    course_id=beginner_course.course_id,
                    title=lesson_title,
                    description=f"Learn about {lesson_title.lower()}",
                    order=j + 1,
                    lesson_type=lesson_type,
                    content=self._generate_lesson_content(lesson_type),
                    duration_minutes=duration,
                    has_quiz="Quiz" in lesson_title
                )
                self.lessons[lesson.lesson_id] = lesson
        
        # Advanced Course
        advanced_course = Course(
            title="Advanced Portfolio Management",
            subtitle="Master professional portfolio strategies",
            description="Deep dive into modern portfolio theory, advanced strategies, and professional portfolio management techniques.",
            category="Portfolio Management",
            tags=["advanced", "portfolio", "strategies", "derivatives", "quantitative"],
            skill_level=SkillLevel.ADVANCED,
            duration_hours=25.0,
            instructor_name="Michael Zhang, CFA",
            instructor_bio="Portfolio Manager, 20+ years Wall Street experience",
            module_count=8,
            lesson_count=40,
            quiz_count=8,
            enrolled_count=456,
            rating=4.9,
            review_count=234,
            prerequisites=["Basic understanding of financial markets", "Elementary statistics"],
            learning_outcomes=[
                "Apply Modern Portfolio Theory in practice",
                "Implement factor-based investing strategies",
                "Use derivatives for hedging and speculation",
                "Conduct quantitative portfolio analysis",
                "Manage institutional portfolios"
            ]
        )
        self.courses[advanced_course.course_id] = advanced_course
        
        # Crypto Course
        crypto_course = Course(
            title="Cryptocurrency Investing Guide",
            subtitle="Navigate the world of digital assets",
            description="Comprehensive guide to understanding and investing in cryptocurrencies, DeFi, and blockchain technology.",
            category="Cryptocurrency",
            tags=["crypto", "bitcoin", "defi", "blockchain", "web3"],
            skill_level=SkillLevel.INTERMEDIATE,
            duration_hours=15.0,
            instructor_name="Alex Kumar",
            instructor_bio="Blockchain Developer & Early Crypto Investor",
            module_count=6,
            lesson_count=30,
            quiz_count=6,
            enrolled_count=2345,
            rating=4.7,
            review_count=890,
            learning_outcomes=[
                "Understand blockchain technology fundamentals",
                "Evaluate different cryptocurrencies",
                "Use crypto exchanges and wallets safely",
                "Explore DeFi protocols and yield farming",
                "Manage crypto portfolio risks"
            ],
            is_featured=True
        )
        self.courses[crypto_course.course_id] = crypto_course
        
    def _generate_lesson_content(self, lesson_type: LessonType) -> Dict[str, Any]:
        """Generate lesson content based on type"""
        if lesson_type == LessonType.VIDEO:
            return {
                "video_url": "https://example.com/video.mp4",
                "transcript": "Video transcript here...",
                "chapters": [
                    {"title": "Introduction", "start_time": 0},
                    {"title": "Main Content", "start_time": 120},
                    {"title": "Summary", "start_time": 600}
                ]
            }
        elif lesson_type == LessonType.ARTICLE:
            return {
                "content": "# Article Title\n\nArticle content in markdown...",
                "reading_time": 10,
                "references": ["Reference 1", "Reference 2"]
            }
        elif lesson_type == LessonType.INTERACTIVE:
            return {
                "type": "quiz",
                "questions": [
                    {
                        "question": "What is compound interest?",
                        "options": ["A", "B", "C", "D"],
                        "correct": 1
                    }
                ]
            }
        elif lesson_type == LessonType.SIMULATION:
            return {
                "simulation_type": "compound_interest_calculator",
                "parameters": {
                    "initial_amount": 1000,
                    "interest_rate": 0.07,
                    "years": 10
                }
            }
        else:
            return {"content": "Lesson content placeholder"}
            
    async def get_courses(
        self,
        category: Optional[str] = None,
        skill_level: Optional[SkillLevel] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Course]:
        """Get courses with filters"""
        courses = list(self.courses.values())
        
        # Filter by category
        if category:
            courses = [c for c in courses if c.category == category]
            
        # Filter by skill level
        if skill_level:
            courses = [c for c in courses if c.skill_level == skill_level]
            
        # Search
        if search:
            search_lower = search.lower()
            courses = [
                c for c in courses
                if search_lower in c.title.lower() or
                search_lower in c.description.lower() or
                any(search_lower in tag for tag in c.tags)
            ]
            
        # Sort by popularity (enrolled count)
        courses.sort(key=lambda c: c.enrolled_count, reverse=True)
        
        # Pagination
        return courses[offset:offset + limit]
        
    async def get_featured_courses(self) -> List[Course]:
        """Get featured courses"""
        featured = [c for c in self.courses.values() if c.is_featured]
        return featured[:6]  # Return top 6 featured courses
        
    async def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        return self.courses.get(course_id)
        
    async def get_course_modules(self, course_id: str) -> List[Module]:
        """Get modules for a course"""
        modules = [
            m for m in self.modules.values()
            if m.course_id == course_id
        ]
        modules.sort(key=lambda m: m.order)
        return modules
        
    async def get_module_lessons(self, module_id: str) -> List[Lesson]:
        """Get lessons for a module"""
        lessons = [
            l for l in self.lessons.values()
            if l.module_id == module_id
        ]
        lessons.sort(key=lambda l: l.order)
        return lessons
        
    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Get lesson by ID"""
        return self.lessons.get(lesson_id)
        
    async def is_enrolled(self, user_id: str, course_id: str) -> bool:
        """Check if user is enrolled in course"""
        user_courses = self.enrollments.get(user_id, set())
        return course_id in user_courses
        
    async def enroll_user(
        self,
        user_id: str,
        course_id: str
    ) -> Dict[str, Any]:
        """Enroll user in course"""
        # Check if course exists
        course = self.courses.get(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
            
        # Add enrollment
        if user_id not in self.enrollments:
            self.enrollments[user_id] = set()
        self.enrollments[user_id].add(course_id)
        
        # Update course enrollment count
        course.enrolled_count += 1
        
        # Initialize progress tracking
        progress_key = (user_id, course_id)
        self.user_progress[progress_key] = {
            "enrolled_at": datetime.now(),
            "modules_completed": 0,
            "lessons_completed": 0,
            "last_accessed": datetime.now()
        }
        
        self.logger.info(f"User {user_id} enrolled in course {course_id}")
        
        return {
            "enrollment_id": f"enr_{user_id}_{course_id}",
            "course_id": course_id,
            "enrolled_at": datetime.now(),
            "status": "active"
        }
        
    async def can_access_lesson(
        self,
        user_id: str,
        lesson_id: str
    ) -> bool:
        """Check if user can access lesson"""
        lesson = self.lessons.get(lesson_id)
        if not lesson:
            return False
            
        # Check enrollment
        return await self.is_enrolled(user_id, lesson.course_id)
        
    async def get_next_lesson(
        self,
        user_id: str,
        lesson_id: str
    ) -> Optional[Lesson]:
        """Get next lesson in sequence"""
        current_lesson = self.lessons.get(lesson_id)
        if not current_lesson:
            return None
            
        # Get all lessons in the same module
        module_lessons = await self.get_module_lessons(current_lesson.module_id)
        
        # Find current lesson index
        current_index = next(
            (i for i, l in enumerate(module_lessons) if l.lesson_id == lesson_id),
            -1
        )
        
        # Return next lesson in module
        if current_index >= 0 and current_index < len(module_lessons) - 1:
            return module_lessons[current_index + 1]
            
        # If last lesson in module, get first lesson of next module
        course_modules = await self.get_course_modules(current_lesson.course_id)
        current_module_index = next(
            (i for i, m in enumerate(course_modules) if m.module_id == current_lesson.module_id),
            -1
        )
        
        if current_module_index >= 0 and current_module_index < len(course_modules) - 1:
            next_module = course_modules[current_module_index + 1]
            next_module_lessons = await self.get_module_lessons(next_module.module_id)
            return next_module_lessons[0] if next_module_lessons else None
            
        return None
        
    async def get_course_count(self) -> int:
        """Get total number of courses"""
        return len(self.courses)
        
    async def get_course_categories(self) -> List[str]:
        """Get all course categories"""
        categories = set(c.category for c in self.courses.values())
        return sorted(list(categories))
        
    async def get_popular_courses(self, limit: int = 10) -> List[Course]:
        """Get most popular courses"""
        courses = list(self.courses.values())
        courses.sort(key=lambda c: c.enrolled_count, reverse=True)
        return courses[:limit]
        
    async def get_new_courses(self, days: int = 30, limit: int = 10) -> List[Course]:
        """Get recently added courses"""
        cutoff_date = datetime.now() - timedelta(days=days)
        new_courses = [
            c for c in self.courses.values()
            if c.created_at >= cutoff_date
        ]
        new_courses.sort(key=lambda c: c.created_at, reverse=True)
        return new_courses[:limit]
        
    async def search_courses(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Course]:
        """Advanced course search"""
        results = []
        query_lower = query.lower()
        
        for course in self.courses.values():
            # Calculate relevance score
            score = 0
            
            # Title match (highest weight)
            if query_lower in course.title.lower():
                score += 10
                
            # Description match
            if query_lower in course.description.lower():
                score += 5
                
            # Tag match
            if any(query_lower in tag for tag in course.tags):
                score += 3
                
            # Instructor match
            if query_lower in course.instructor_name.lower():
                score += 2
                
            if score > 0:
                results.append((score, course))
                
        # Sort by relevance
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Apply additional filters
        courses = [c for _, c in results]
        
        if filters:
            if "category" in filters:
                courses = [c for c in courses if c.category == filters["category"]]
            if "skill_level" in filters:
                courses = [c for c in courses if c.skill_level == filters["skill_level"]]
            if "max_duration" in filters:
                courses = [c for c in courses if c.duration_hours <= filters["max_duration"]]
                
        return courses
        
    async def get_course_recommendations(
        self,
        user_id: str,
        completed_courses: List[str],
        limit: int = 5
    ) -> List[Course]:
        """Get course recommendations based on completed courses"""
        # In production, use ML recommendation engine
        
        # Simple rule-based recommendations
        recommendations = []
        completed_categories = set()
        completed_levels = set()
        
        for course_id in completed_courses:
            course = self.courses.get(course_id)
            if course:
                completed_categories.add(course.category)
                completed_levels.add(course.skill_level)
                
        # Recommend courses in same categories but higher level
        for course in self.courses.values():
            if course.course_id in completed_courses:
                continue
                
            score = 0
            
            # Same category
            if course.category in completed_categories:
                score += 3
                
            # Next skill level
            if course.skill_level.value > max(
                (l.value for l in completed_levels),
                default=0
            ):
                score += 2
                
            # Popular courses
            if course.enrolled_count > 1000:
                score += 1
                
            if score > 0:
                recommendations.append((score, course))
                
        # Sort by score
        recommendations.sort(key=lambda x: x[0], reverse=True)
        
        return [c for _, c in recommendations[:limit]] 