"""
Data models for Education Hub Service
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import uuid


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LessonType(str, Enum):
    VIDEO = "video"
    ARTICLE = "article"
    INTERACTIVE = "interactive"
    SIMULATION = "simulation"
    CASE_STUDY = "case_study"
    WORKSHOP = "workshop"


class QuizType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    ESSAY = "essay"
    CALCULATION = "calculation"


class ResourceType(str, Enum):
    EBOOK = "ebook"
    TEMPLATE = "template"
    CALCULATOR = "calculator"
    CHECKLIST = "checklist"
    GUIDE = "guide"
    INFOGRAPHIC = "infographic"
    RESEARCH = "research"


class WebinarStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AchievementType(str, Enum):
    COURSE_COMPLETE = "course_complete"
    MODULE_COMPLETE = "module_complete"
    QUIZ_PERFECT = "quiz_perfect"
    STREAK = "streak"
    MILESTONE = "milestone"
    CERTIFICATION = "certification"


class Course(BaseModel):
    """Course information"""
    course_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic info
    title: str
    subtitle: Optional[str] = None
    description: str
    category: str
    tags: List[str] = []
    
    # Course details
    skill_level: SkillLevel
    duration_hours: float
    language: str = "English"
    
    # Instructor
    instructor_name: str
    instructor_bio: Optional[str] = None
    instructor_avatar: Optional[str] = None
    
    # Content
    module_count: int = 0
    lesson_count: int = 0
    quiz_count: int = 0
    
    # Enrollment
    enrolled_count: int = 0
    rating: Optional[float] = None
    review_count: int = 0
    
    # Pricing (for future premium courses)
    is_free: bool = True
    price: Optional[Decimal] = None
    
    # Features
    has_certificate: bool = True
    has_discussions: bool = True
    has_assignments: bool = False
    
    # Images
    thumbnail_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    
    # Prerequisites
    prerequisites: List[str] = []
    
    # Outcomes
    learning_outcomes: List[str] = []
    
    # Status
    is_published: bool = True
    is_featured: bool = False
    
    # User specific (populated in queries)
    is_enrolled: Optional[bool] = None
    user_progress: Optional['Progress'] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError("Rating must be between 0 and 5")
        return v


class Module(BaseModel):
    """Course module"""
    module_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    course_id: str
    
    # Basic info
    title: str
    description: str
    order: int
    
    # Content
    lesson_count: int = 0
    quiz_count: int = 0
    estimated_time_minutes: int
    
    # Requirements
    is_locked: bool = False
    unlock_requirements: Optional[Dict[str, Any]] = None
    
    # User specific
    progress: Optional['ModuleProgress'] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)


class Lesson(BaseModel):
    """Course lesson"""
    lesson_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    module_id: str
    course_id: str
    
    # Basic info
    title: str
    description: str
    order: int
    
    # Content
    lesson_type: LessonType
    content: Dict[str, Any]  # Varies by type
    
    # Duration
    duration_minutes: int
    
    # Resources
    resources: List[Dict[str, str]] = []  # Additional downloads
    
    # Interactive elements
    has_quiz: bool = False
    quiz_id: Optional[str] = None
    has_exercise: bool = False
    exercise_data: Optional[Dict[str, Any]] = None
    
    # Tracking
    is_required: bool = True
    completion_criteria: Dict[str, Any] = {"view_percentage": 80}
    
    # User specific
    is_completed: Optional[bool] = None
    last_viewed_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Quiz(BaseModel):
    """Quiz/Assessment"""
    quiz_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Association
    course_id: Optional[str] = None
    module_id: Optional[str] = None
    lesson_id: Optional[str] = None
    
    # Basic info
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    
    # Configuration
    question_count: int
    passing_score: float = 70.0  # Percentage
    time_limit_minutes: Optional[int] = None
    max_attempts: Optional[int] = 3
    
    # Options
    randomize_questions: bool = True
    randomize_options: bool = True
    show_correct_answers: bool = True
    show_explanations: bool = True
    
    # Difficulty
    difficulty_level: SkillLevel = SkillLevel.BEGINNER
    
    # User specific
    user_attempts: Optional[List['QuizAttempt']] = None
    best_score: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('passing_score')
    def validate_passing_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Passing score must be between 0 and 100")
        return v


class QuizQuestion(BaseModel):
    """Quiz question"""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quiz_id: str
    
    # Question
    question_type: QuizType
    question_text: str
    question_image: Optional[str] = None
    
    # Options (for multiple choice/matching)
    options: Optional[List[Dict[str, Any]]] = None
    
    # Answer
    correct_answer: Union[str, List[str], Dict[str, Any]]
    explanation: Optional[str] = None
    
    # Scoring
    points: int = 1
    partial_credit: bool = False
    
    # Order
    order: int
    
    # Metadata
    tags: List[str] = []
    difficulty: int = Field(1, ge=1, le=5)


class QuizAttempt(BaseModel):
    """Quiz attempt record"""
    attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quiz_id: str
    user_id: str
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    time_spent_seconds: Optional[int] = None
    
    # Answers
    answers: Dict[str, Any] = {}  # question_id -> answer
    
    # Results
    score: Optional[float] = None
    passed: Optional[bool] = None
    
    # Review
    reviewed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    
    # Status
    is_completed: bool = False
    
    @property
    def time_limit(self) -> Optional[datetime]:
        """Calculate time limit if applicable"""
        # Would fetch from quiz config
        return None


class LearningPath(BaseModel):
    """Personalized learning path"""
    path_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Goals
    learning_goals: List['LearningGoal']
    
    # Current status
    current_skill_level: SkillLevel
    target_skill_level: SkillLevel
    
    # Recommended courses
    recommended_courses: List[str] = []  # course_ids
    completed_courses: List[str] = []
    in_progress_courses: List[str] = []
    
    # Progress
    overall_progress: float = 0.0
    estimated_completion_date: Optional[datetime] = None
    
    # Milestones
    milestones: List[Dict[str, Any]] = []
    next_milestone: Optional[Dict[str, Any]] = None
    
    # Customization
    preferred_lesson_types: List[LessonType] = []
    time_commitment_hours_per_week: float = 5.0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LearningGoal(BaseModel):
    """Individual learning goal"""
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Goal details
    title: str
    description: Optional[str] = None
    category: str
    
    # Target
    target_date: Optional[datetime] = None
    skill_level_target: Optional[SkillLevel] = None
    
    # Related content
    related_courses: List[str] = []
    related_skills: List[str] = []
    
    # Progress
    is_completed: bool = False
    progress: float = 0.0
    
    # Priority
    priority: int = Field(1, ge=1, le=5)


class Progress(BaseModel):
    """Overall course progress"""
    user_id: str
    course_id: str
    
    # Completion
    modules_completed: int = 0
    total_modules: int
    lessons_completed: int = 0
    total_lessons: int
    
    # Performance
    average_quiz_score: Optional[float] = None
    quizzes_passed: int = 0
    total_quizzes: int = 0
    
    # Time
    total_time_spent_minutes: int = 0
    last_accessed_at: datetime = Field(default_factory=datetime.now)
    
    # Status
    completion_percentage: float = 0.0
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    
    # Current position
    current_module_id: Optional[str] = None
    current_lesson_id: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Check if actively learning"""
        return (datetime.now() - self.last_accessed_at).days < 7


class ModuleProgress(BaseModel):
    """Module-level progress"""
    user_id: str
    module_id: str
    
    # Completion
    lessons_completed: int = 0
    total_lessons: int
    
    # Status
    is_unlocked: bool = True
    is_completed: bool = False
    completion_percentage: float = 0.0
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Certificate(BaseModel):
    """Course completion certificate"""
    certificate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    
    # Certificate details
    certificate_number: str
    course_title: str
    user_name: str
    
    # Achievement
    completion_date: datetime
    final_score: Optional[float] = None
    total_hours: float
    
    # Verification
    verification_url: str
    is_verified: bool = True
    
    # PDF
    pdf_url: Optional[str] = None
    
    # Metadata
    issued_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class Achievement(BaseModel):
    """Learning achievement/badge"""
    achievement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Achievement details
    achievement_type: AchievementType
    title: str
    description: str
    icon_url: str
    
    # Criteria
    criteria: Dict[str, Any]
    
    # Context
    course_id: Optional[str] = None
    related_data: Optional[Dict[str, Any]] = None
    
    # Timestamps
    earned_at: datetime = Field(default_factory=datetime.now)


class Resource(BaseModel):
    """Educational resource"""
    resource_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic info
    title: str
    description: str
    resource_type: ResourceType
    
    # Categories
    category: str
    tags: List[str] = []
    skill_level: Optional[SkillLevel] = None
    
    # Content
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    
    # Usage
    download_count: int = 0
    rating: Optional[float] = None
    
    # Access
    is_free: bool = True
    requires_enrollment: bool = False
    related_courses: List[str] = []
    
    # Metadata
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class GlossaryTerm(BaseModel):
    """Financial term definition"""
    term_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Term
    term: str
    aliases: List[str] = []
    
    # Definition
    definition: str
    extended_definition: Optional[str] = None
    
    # Examples
    examples: List[str] = []
    
    # Relations
    category: str
    related_terms: List[str] = []
    
    # References
    sources: List[str] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)


class Webinar(BaseModel):
    """Live webinar/workshop"""
    webinar_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic info
    title: str
    description: str
    topic: str
    
    # Instructor
    instructor_name: str
    instructor_bio: Optional[str] = None
    instructor_avatar: Optional[str] = None
    
    # Schedule
    scheduled_at: datetime
    duration_minutes: int
    timezone: str = "UTC"
    
    # Access
    max_attendees: Optional[int] = None
    registered_count: int = 0
    
    # Links
    registration_url: Optional[str] = None
    meeting_url: Optional[str] = None
    recording_url: Optional[str] = None
    
    # Status
    status: WebinarStatus = WebinarStatus.SCHEDULED
    
    # User specific
    is_registered: Optional[bool] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)


class Discussion(BaseModel):
    """Course discussion thread"""
    discussion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    course_id: str
    user_id: str
    
    # Content
    title: str
    content: str
    
    # Author
    author_name: str
    author_avatar: Optional[str] = None
    
    # Engagement
    reply_count: int = 0
    like_count: int = 0
    view_count: int = 0
    
    # Status
    is_pinned: bool = False
    is_resolved: bool = False
    is_instructor_response: bool = False
    
    # User specific
    user_liked: Optional[bool] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_reply_at: Optional[datetime] = None


class LearningAnalytics(BaseModel):
    """User learning analytics"""
    user_id: str
    
    # Activity
    total_courses_enrolled: int
    total_courses_completed: int
    current_streak_days: int
    longest_streak_days: int
    
    # Time
    total_learning_hours: float
    average_daily_minutes: float
    most_active_hour: int  # 0-23
    most_active_day: str  # day of week
    
    # Performance
    average_quiz_score: float
    quiz_improvement_rate: float
    
    # Preferences
    preferred_lesson_types: List[LessonType]
    preferred_categories: List[str]
    preferred_learning_time: str  # morning/afternoon/evening
    
    # Engagement
    discussion_posts: int
    helpful_votes_received: int
    
    # Achievements
    total_achievements: int
    total_certificates: int
    
    # Recommendations accuracy
    recommendation_click_rate: float
    recommendation_completion_rate: float
    
    # Calculated at
    calculated_at: datetime = Field(default_factory=datetime.now) 