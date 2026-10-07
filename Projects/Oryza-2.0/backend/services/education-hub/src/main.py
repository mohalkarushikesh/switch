"""
Education Hub - Financial education and learning platform
"""
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

# Import from shared modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.config.settings import get_settings
from shared.database.connection import init_databases, close_databases, get_db, get_redis
from shared.database.models import User
from shared.utils.logger import ServiceLogger
from shared.utils.auth import get_current_verified_user

# Import education modules
from .course_manager import CourseManager
from .learning_engine import LearningEngine
from .quiz_system import QuizSystem
from .content_library import ContentLibrary
from .models import (
    Course, Module, Lesson, LessonType,
    Quiz, QuizQuestion, QuizAttempt,
    LearningPath, LearningGoal, SkillLevel,
    Progress, Certificate, Achievement,
    Resource, ResourceType, Discussion,
    Webinar, WebinarStatus
)

settings = get_settings()
education_logger = ServiceLogger("education-hub")
logger = education_logger.get_logger()

# Global instances
course_manager = None
learning_engine = None
quiz_system = None
content_library = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global course_manager, learning_engine, quiz_system, content_library
    
    # Startup
    logger.info("Starting Education Hub Service")
    await init_databases()
    
    # Initialize components
    course_manager = CourseManager()
    learning_engine = LearningEngine()
    quiz_system = QuizSystem()
    content_library = ContentLibrary()
    
    await asyncio.gather(
        course_manager.initialize(),
        learning_engine.initialize(),
        quiz_system.initialize(),
        content_library.initialize()
    )
    
    # Start background tasks
    asyncio.create_task(learning_engine.update_recommendations())
    
    logger.info("Education Hub Service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Education Hub Service")
    await close_databases()


# Create FastAPI app
app = FastAPI(
    title="Education Hub Service",
    description="Financial education and learning platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Education Hub",
        "version": "1.0.0",
        "status": "operational",
        "capabilities": [
            "Interactive courses",
            "Personalized learning paths",
            "Quizzes and assessments",
            "Progress tracking",
            "Certificates",
            "Resource library",
            "Community discussions",
            "Expert webinars"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "course_manager": "ready" if course_manager else "not initialized",
            "learning_engine": "ready" if learning_engine else "not initialized",
            "quiz_system": "ready" if quiz_system else "not initialized",
            "content_library": "ready" if content_library else "not initialized"
        },
        "total_courses": await course_manager.get_course_count() if course_manager else 0,
        "active_learners": await learning_engine.get_active_learner_count() if learning_engine else 0
    }


@app.get("/courses", response_model=List[Course])
async def get_courses(
    category: Optional[str] = None,
    skill_level: Optional[SkillLevel] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Browse available courses"""
    try:
        courses = await course_manager.get_courses(
            category=category,
            skill_level=skill_level,
            search=search,
            limit=limit,
            offset=offset
        )
        
        return courses
        
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch courses: {str(e)}"
        )


@app.get("/courses/featured", response_model=List[Course])
async def get_featured_courses():
    """Get featured courses"""
    try:
        courses = await course_manager.get_featured_courses()
        return courses
        
    except Exception as e:
        logger.error(f"Error fetching featured courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch featured courses: {str(e)}"
        )


@app.get("/courses/{course_id}", response_model=Course)
async def get_course_details(
    course_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get detailed course information"""
    try:
        course = await course_manager.get_course(course_id)
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
            
        # Add user enrollment status
        course.is_enrolled = await course_manager.is_enrolled(
            user_id=str(current_user.id),
            course_id=course_id
        )
        
        # Add user progress if enrolled
        if course.is_enrolled:
            progress = await learning_engine.get_course_progress(
                user_id=str(current_user.id),
                course_id=course_id
            )
            course.user_progress = progress
            
        return course
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch course: {str(e)}"
        )


@app.post("/courses/{course_id}/enroll")
async def enroll_in_course(
    course_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Enroll in a course"""
    try:
        # Check if already enrolled
        if await course_manager.is_enrolled(str(current_user.id), course_id):
            return {
                "status": "already_enrolled",
                "message": "You are already enrolled in this course"
            }
            
        # Enroll user
        enrollment = await course_manager.enroll_user(
            user_id=str(current_user.id),
            course_id=course_id
        )
        
        # Create learning path entry
        await learning_engine.add_to_learning_path(
            user_id=str(current_user.id),
            course_id=course_id
        )
        
        return {
            "status": "success",
            "enrollment": enrollment,
            "message": "Successfully enrolled in course"
        }
        
    except Exception as e:
        logger.error(f"Error enrolling in course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll: {str(e)}"
        )


@app.get("/courses/{course_id}/modules", response_model=List[Module])
async def get_course_modules(
    course_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get course modules"""
    try:
        # Check enrollment
        if not await course_manager.is_enrolled(str(current_user.id), course_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled to access course content"
            )
            
        modules = await course_manager.get_course_modules(course_id)
        
        # Add progress for each module
        for module in modules:
            module.progress = await learning_engine.get_module_progress(
                user_id=str(current_user.id),
                module_id=module.module_id
            )
            
        return modules
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching modules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch modules: {str(e)}"
        )


@app.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get lesson content"""
    try:
        lesson = await course_manager.get_lesson(lesson_id)
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
            
        # Check access
        if not await course_manager.can_access_lesson(str(current_user.id), lesson_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this lesson"
            )
            
        # Track lesson view
        await learning_engine.track_lesson_view(
            user_id=str(current_user.id),
            lesson_id=lesson_id
        )
        
        return lesson
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch lesson: {str(e)}"
        )


@app.post("/lessons/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: str,
    time_spent: int,  # seconds
    current_user: User = Depends(get_current_verified_user)
):
    """Mark lesson as complete"""
    try:
        # Record completion
        completion = await learning_engine.complete_lesson(
            user_id=str(current_user.id),
            lesson_id=lesson_id,
            time_spent=time_spent
        )
        
        # Check for module/course completion
        achievements = await learning_engine.check_achievements(
            user_id=str(current_user.id),
            lesson_id=lesson_id
        )
        
        return {
            "status": "success",
            "completion": completion,
            "achievements": achievements,
            "next_lesson": await course_manager.get_next_lesson(
                user_id=str(current_user.id),
                lesson_id=lesson_id
            )
        }
        
    except Exception as e:
        logger.error(f"Error completing lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete lesson: {str(e)}"
        )


@app.get("/quizzes/{quiz_id}", response_model=Quiz)
async def get_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Get quiz details"""
    try:
        quiz = await quiz_system.get_quiz(quiz_id)
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
            
        # Check access
        if not await quiz_system.can_access_quiz(str(current_user.id), quiz_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this quiz"
            )
            
        # Add attempt history
        quiz.user_attempts = await quiz_system.get_user_attempts(
            user_id=str(current_user.id),
            quiz_id=quiz_id
        )
        
        return quiz
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch quiz: {str(e)}"
        )


@app.post("/quizzes/{quiz_id}/attempt")
async def start_quiz_attempt(
    quiz_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Start a quiz attempt"""
    try:
        # Check if can attempt
        can_attempt, reason = await quiz_system.can_attempt_quiz(
            user_id=str(current_user.id),
            quiz_id=quiz_id
        )
        
        if not can_attempt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )
            
        # Create attempt
        attempt = await quiz_system.create_attempt(
            user_id=str(current_user.id),
            quiz_id=quiz_id
        )
        
        # Get questions (without answers)
        questions = await quiz_system.get_quiz_questions(
            quiz_id=quiz_id,
            hide_answers=True
        )
        
        return {
            "attempt_id": attempt.attempt_id,
            "questions": questions,
            "time_limit": attempt.time_limit,
            "started_at": attempt.started_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start quiz: {str(e)}"
        )


@app.post("/quizzes/attempts/{attempt_id}/submit")
async def submit_quiz_attempt(
    attempt_id: str,
    answers: List[Dict[str, Any]],
    current_user: User = Depends(get_current_verified_user)
):
    """Submit quiz answers"""
    try:
        # Validate attempt
        attempt = await quiz_system.get_attempt(attempt_id)
        
        if not attempt or attempt.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt not found"
            )
            
        if attempt.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz already submitted"
            )
            
        # Grade quiz
        result = await quiz_system.grade_quiz(
            attempt_id=attempt_id,
            answers=answers
        )
        
        # Update progress
        await learning_engine.update_quiz_progress(
            user_id=str(current_user.id),
            quiz_id=attempt.quiz_id,
            score=result["score"]
        )
        
        # Check for achievements
        achievements = await learning_engine.check_quiz_achievements(
            user_id=str(current_user.id),
            quiz_id=attempt.quiz_id,
            score=result["score"]
        )
        
        return {
            "result": result,
            "achievements": achievements,
            "certificate": result.get("certificate")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit quiz: {str(e)}"
        )


@app.get("/learning-path", response_model=LearningPath)
async def get_learning_path(
    current_user: User = Depends(get_current_verified_user)
):
    """Get personalized learning path"""
    try:
        path = await learning_engine.get_learning_path(str(current_user.id))
        
        if not path:
            # Create initial learning path
            path = await learning_engine.create_learning_path(
                user_id=str(current_user.id),
                goals=await learning_engine.assess_learning_goals(str(current_user.id))
            )
            
        return path
        
    except Exception as e:
        logger.error(f"Error fetching learning path: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch learning path: {str(e)}"
        )


@app.put("/learning-path/goals")
async def update_learning_goals(
    goals: List[LearningGoal],
    current_user: User = Depends(get_current_verified_user)
):
    """Update learning goals"""
    try:
        updated_path = await learning_engine.update_learning_goals(
            user_id=str(current_user.id),
            goals=goals
        )
        
        # Get new recommendations
        recommendations = await learning_engine.get_course_recommendations(
            user_id=str(current_user.id),
            limit=5
        )
        
        return {
            "status": "success",
            "learning_path": updated_path,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error updating goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goals: {str(e)}"
        )


@app.get("/progress/overview")
async def get_progress_overview(
    current_user: User = Depends(get_current_verified_user)
):
    """Get overall learning progress"""
    try:
        overview = await learning_engine.get_progress_overview(
            user_id=str(current_user.id)
        )
        
        return overview
        
    except Exception as e:
        logger.error(f"Error fetching progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch progress: {str(e)}"
        )


@app.get("/achievements", response_model=List[Achievement])
async def get_achievements(
    current_user: User = Depends(get_current_verified_user)
):
    """Get user achievements"""
    try:
        achievements = await learning_engine.get_user_achievements(
            user_id=str(current_user.id)
        )
        
        return achievements
        
    except Exception as e:
        logger.error(f"Error fetching achievements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch achievements: {str(e)}"
        )


@app.get("/certificates", response_model=List[Certificate])
async def get_certificates(
    current_user: User = Depends(get_current_verified_user)
):
    """Get earned certificates"""
    try:
        certificates = await learning_engine.get_user_certificates(
            user_id=str(current_user.id)
        )
        
        return certificates
        
    except Exception as e:
        logger.error(f"Error fetching certificates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch certificates: {str(e)}"
        )


@app.get("/resources", response_model=List[Resource])
async def get_resources(
    resource_type: Optional[ResourceType] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Browse resource library"""
    try:
        resources = await content_library.get_resources(
            resource_type=resource_type,
            category=category,
            search=search,
            limit=limit,
            offset=offset
        )
        
        return resources
        
    except Exception as e:
        logger.error(f"Error fetching resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch resources: {str(e)}"
        )


@app.get("/glossary")
async def search_glossary(
    term: str,
    limit: int = 10
):
    """Search financial glossary"""
    try:
        results = await content_library.search_glossary(
            term=term,
            limit=limit
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching glossary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search glossary: {str(e)}"
        )


@app.get("/webinars", response_model=List[Webinar])
async def get_webinars(
    status: Optional[WebinarStatus] = None,
    upcoming_only: bool = True
):
    """Get webinar schedule"""
    try:
        webinars = await content_library.get_webinars(
            status=status,
            upcoming_only=upcoming_only
        )
        
        return webinars
        
    except Exception as e:
        logger.error(f"Error fetching webinars: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch webinars: {str(e)}"
        )


@app.post("/webinars/{webinar_id}/register")
async def register_for_webinar(
    webinar_id: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Register for a webinar"""
    try:
        registration = await content_library.register_for_webinar(
            user_id=str(current_user.id),
            webinar_id=webinar_id
        )
        
        return {
            "status": "success",
            "registration": registration,
            "message": "Successfully registered for webinar"
        }
        
    except Exception as e:
        logger.error(f"Error registering for webinar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register: {str(e)}"
        )


@app.get("/discussions/{course_id}")
async def get_course_discussions(
    course_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_verified_user)
):
    """Get course discussions"""
    try:
        # Check enrollment
        if not await course_manager.is_enrolled(str(current_user.id), course_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled to access discussions"
            )
            
        discussions = await content_library.get_discussions(
            course_id=course_id,
            limit=limit,
            offset=offset
        )
        
        return discussions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discussions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch discussions: {str(e)}"
        )


@app.post("/discussions")
async def create_discussion(
    course_id: str,
    title: str,
    content: str,
    current_user: User = Depends(get_current_verified_user)
) -> Discussion:
    """Create a new discussion"""
    try:
        # Check enrollment
        if not await course_manager.is_enrolled(str(current_user.id), course_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled to create discussions"
            )
            
        discussion = await content_library.create_discussion(
            user_id=str(current_user.id),
            course_id=course_id,
            title=title,
            content=content
        )
        
        return discussion
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating discussion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create discussion: {str(e)}"
        )


@app.get("/recommendations")
async def get_recommendations(
    limit: int = 5,
    current_user: User = Depends(get_current_verified_user)
):
    """Get personalized course recommendations"""
    try:
        recommendations = await learning_engine.get_course_recommendations(
            user_id=str(current_user.id),
            limit=limit
        )
        
        return {
            "recommendations": recommendations,
            "based_on": {
                "learning_goals": await learning_engine.get_user_goals(str(current_user.id)),
                "skill_level": await learning_engine.assess_skill_level(str(current_user.id)),
                "interests": await learning_engine.get_user_interests(str(current_user.id))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8014,
        reload=True
    ) 