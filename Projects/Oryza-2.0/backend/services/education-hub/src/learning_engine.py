"""
Learning Engine - Personalized learning and progress tracking
"""
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import statistics

from .models import (
    LearningPath, LearningGoal, Progress, ModuleProgress,
    Achievement, AchievementType, Certificate, SkillLevel,
    LearningAnalytics
)


class LearningEngine:
    """
    Manages personalized learning paths and progress tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger("learning_engine")
        self.learning_paths = {}  # user_id -> LearningPath
        self.user_progress = {}  # (user_id, course_id) -> Progress
        self.module_progress = {}  # (user_id, module_id) -> ModuleProgress
        self.achievements = defaultdict(list)  # user_id -> List[Achievement]
        self.certificates = defaultdict(list)  # user_id -> List[Certificate]
        self.lesson_views = defaultdict(list)  # user_id -> List[lesson_view_data]
        self.user_goals = defaultdict(list)  # user_id -> List[LearningGoal]
        self.is_updating = False
        
    async def initialize(self):
        """Initialize learning engine"""
        self.logger.info("Initializing Learning Engine")
        
        # In production:
        # - Connect to analytics database
        # - Load ML recommendation models
        # - Initialize progress tracking systems
        
    async def update_recommendations(self):
        """Update learning recommendations periodically"""
        self.is_updating = True
        self.logger.info("Started recommendation updates")
        
        while self.is_updating:
            try:
                # Update recommendations for active users
                await self._update_active_user_recommendations()
                
                # Analyze learning patterns
                await self._analyze_learning_patterns()
                
                # Check for milestone achievements
                await self._check_milestone_achievements()
                
                await asyncio.sleep(3600)  # Update hourly
                
            except Exception as e:
                self.logger.error(f"Error updating recommendations: {str(e)}")
                await asyncio.sleep(300)
                
    async def _update_active_user_recommendations(self):
        """Update recommendations for active users"""
        # In production, identify active users and update their paths
        pass
        
    async def _analyze_learning_patterns(self):
        """Analyze user learning patterns"""
        # In production, run analytics on learning behavior
        pass
        
    async def _check_milestone_achievements(self):
        """Check for milestone achievements"""
        # In production, check for users reaching milestones
        pass
        
    async def create_learning_path(
        self,
        user_id: str,
        goals: List[LearningGoal]
    ) -> LearningPath:
        """Create personalized learning path"""
        # Assess current skill level
        skill_level = await self.assess_skill_level(user_id)
        
        # Determine target skill level from goals
        target_level = SkillLevel.INTERMEDIATE
        if any("advanced" in g.title.lower() for g in goals):
            target_level = SkillLevel.ADVANCED
        elif any("expert" in g.title.lower() for g in goals):
            target_level = SkillLevel.EXPERT
            
        # Create learning path
        path = LearningPath(
            user_id=user_id,
            learning_goals=goals,
            current_skill_level=skill_level,
            target_skill_level=target_level,
            recommended_courses=await self._get_recommended_course_ids(user_id, goals),
            milestones=[
                {
                    "title": "Complete First Course",
                    "description": "Finish your first course",
                    "target_date": datetime.now() + timedelta(days=30),
                    "completed": False
                },
                {
                    "title": "Pass 5 Quizzes",
                    "description": "Pass 5 quizzes with 80% or higher",
                    "target_date": datetime.now() + timedelta(days=60),
                    "completed": False
                }
            ]
        )
        
        self.learning_paths[user_id] = path
        self.user_goals[user_id] = goals
        
        return path
        
    async def get_learning_path(self, user_id: str) -> Optional[LearningPath]:
        """Get user's learning path"""
        return self.learning_paths.get(user_id)
        
    async def update_learning_goals(
        self,
        user_id: str,
        goals: List[LearningGoal]
    ) -> LearningPath:
        """Update learning goals"""
        path = self.learning_paths.get(user_id)
        
        if not path:
            return await self.create_learning_path(user_id, goals)
            
        # Update goals
        path.learning_goals = goals
        self.user_goals[user_id] = goals
        
        # Recalculate recommendations
        path.recommended_courses = await self._get_recommended_course_ids(user_id, goals)
        path.updated_at = datetime.now()
        
        return path
        
    async def add_to_learning_path(
        self,
        user_id: str,
        course_id: str
    ):
        """Add course to learning path"""
        path = self.learning_paths.get(user_id)
        if path:
            if course_id not in path.in_progress_courses:
                path.in_progress_courses.append(course_id)
                
    async def get_course_progress(
        self,
        user_id: str,
        course_id: str
    ) -> Progress:
        """Get course progress"""
        key = (user_id, course_id)
        
        if key not in self.user_progress:
            # Create initial progress
            self.user_progress[key] = Progress(
                user_id=user_id,
                course_id=course_id,
                total_modules=5,  # Would fetch from course
                total_lessons=25  # Would fetch from course
            )
            
        return self.user_progress[key]
        
    async def get_module_progress(
        self,
        user_id: str,
        module_id: str
    ) -> ModuleProgress:
        """Get module progress"""
        key = (user_id, module_id)
        
        if key not in self.module_progress:
            # Create initial progress
            self.module_progress[key] = ModuleProgress(
                user_id=user_id,
                module_id=module_id,
                total_lessons=5  # Would fetch from module
            )
            
        return self.module_progress[key]
        
    async def track_lesson_view(
        self,
        user_id: str,
        lesson_id: str
    ):
        """Track lesson view"""
        view_data = {
            "lesson_id": lesson_id,
            "viewed_at": datetime.now(),
            "device": "web",  # Would detect from request
            "session_id": f"session_{datetime.now().timestamp()}"
        }
        
        self.lesson_views[user_id].append(view_data)
        
    async def complete_lesson(
        self,
        user_id: str,
        lesson_id: str,
        time_spent: int
    ) -> Dict[str, Any]:
        """Mark lesson as complete"""
        # In production:
        # - Update database
        # - Calculate progress
        # - Check for achievements
        
        # Mock implementation
        completion = {
            "lesson_id": lesson_id,
            "completed_at": datetime.now(),
            "time_spent_seconds": time_spent,
            "completion_rate": 1.0
        }
        
        # Update course progress
        # This would need actual course/module/lesson relationships
        
        self.logger.info(f"User {user_id} completed lesson {lesson_id}")
        
        return completion
        
    async def check_achievements(
        self,
        user_id: str,
        lesson_id: str
    ) -> List[Achievement]:
        """Check for new achievements"""
        new_achievements = []
        
        # Check various achievement criteria
        # In production, would have complex achievement rules
        
        # Example: First lesson completed
        user_achievements = self.achievements[user_id]
        has_first_lesson = any(
            a.achievement_type == AchievementType.MILESTONE and
            a.title == "First Steps"
            for a in user_achievements
        )
        
        if not has_first_lesson:
            achievement = Achievement(
                user_id=user_id,
                achievement_type=AchievementType.MILESTONE,
                title="First Steps",
                description="Completed your first lesson",
                icon_url="/achievements/first_steps.png",
                criteria={"lessons_completed": 1}
            )
            
            self.achievements[user_id].append(achievement)
            new_achievements.append(achievement)
            
        return new_achievements
        
    async def update_quiz_progress(
        self,
        user_id: str,
        quiz_id: str,
        score: float
    ):
        """Update progress after quiz completion"""
        # In production, update various progress metrics
        
        # Check for quiz achievements
        if score == 100.0:
            await self._award_perfect_quiz_achievement(user_id, quiz_id)
            
    async def _award_perfect_quiz_achievement(
        self,
        user_id: str,
        quiz_id: str
    ):
        """Award achievement for perfect quiz score"""
        achievement = Achievement(
            user_id=user_id,
            achievement_type=AchievementType.QUIZ_PERFECT,
            title="Perfect Score!",
            description="Scored 100% on a quiz",
            icon_url="/achievements/perfect_score.png",
            criteria={"quiz_id": quiz_id, "score": 100},
            related_data={"quiz_id": quiz_id}
        )
        
        self.achievements[user_id].append(achievement)
        
    async def check_quiz_achievements(
        self,
        user_id: str,
        quiz_id: str,
        score: float
    ) -> List[Achievement]:
        """Check for quiz-related achievements"""
        new_achievements = []
        
        # Perfect score
        if score == 100.0:
            achievement = Achievement(
                user_id=user_id,
                achievement_type=AchievementType.QUIZ_PERFECT,
                title="Perfect Score!",
                description="Achieved 100% on a quiz",
                icon_url="/achievements/perfect_quiz.png",
                criteria={"score": 100},
                related_data={"quiz_id": quiz_id}
            )
            new_achievements.append(achievement)
            
        # Add to achievements
        self.achievements[user_id].extend(new_achievements)
        
        return new_achievements
        
    async def get_progress_overview(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get overall learning progress"""
        # Calculate various metrics
        user_achievements = self.achievements.get(user_id, [])
        user_certificates = self.certificates.get(user_id, [])
        
        # Get learning path
        path = self.learning_paths.get(user_id)
        
        # Calculate streaks
        streak_data = await self._calculate_learning_streak(user_id)
        
        return {
            "total_courses_enrolled": len(path.in_progress_courses + path.completed_courses) if path else 0,
            "total_courses_completed": len(path.completed_courses) if path else 0,
            "current_streak_days": streak_data["current"],
            "longest_streak_days": streak_data["longest"],
            "total_achievements": len(user_achievements),
            "total_certificates": len(user_certificates),
            "total_learning_hours": await self._calculate_total_learning_hours(user_id),
            "skill_level": path.current_skill_level if path else SkillLevel.BEGINNER,
            "next_milestone": path.next_milestone if path else None,
            "recent_activity": await self._get_recent_activity(user_id)
        }
        
    async def _calculate_learning_streak(
        self,
        user_id: str
    ) -> Dict[str, int]:
        """Calculate learning streak"""
        # In production, calculate from activity logs
        return {
            "current": 7,
            "longest": 15
        }
        
    async def _calculate_total_learning_hours(
        self,
        user_id: str
    ) -> float:
        """Calculate total learning hours"""
        # In production, sum from all completed lessons
        return 42.5
        
    async def _get_recent_activity(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get recent learning activity"""
        # In production, fetch from activity log
        return [
            {
                "type": "lesson_completed",
                "title": "Understanding Risk vs Return",
                "timestamp": datetime.now() - timedelta(hours=2)
            },
            {
                "type": "quiz_passed",
                "title": "Module 1 Quiz",
                "score": 85,
                "timestamp": datetime.now() - timedelta(days=1)
            }
        ]
        
    async def get_user_achievements(
        self,
        user_id: str
    ) -> List[Achievement]:
        """Get user achievements"""
        return self.achievements.get(user_id, [])
        
    async def get_user_certificates(
        self,
        user_id: str
    ) -> List[Certificate]:
        """Get user certificates"""
        return self.certificates.get(user_id, [])
        
    async def issue_certificate(
        self,
        user_id: str,
        course_id: str,
        course_title: str,
        final_score: float,
        total_hours: float
    ) -> Certificate:
        """Issue course completion certificate"""
        # Generate certificate
        certificate = Certificate(
            user_id=user_id,
            course_id=course_id,
            certificate_number=f"ORYZA-{datetime.now().year}-{len(self.certificates[user_id]) + 1:04d}",
            course_title=course_title,
            user_name="User Name",  # Would fetch from user profile
            completion_date=datetime.now(),
            final_score=final_score,
            total_hours=total_hours,
            verification_url=f"https://oryza.com/verify/{user_id}-{course_id}"
        )
        
        self.certificates[user_id].append(certificate)
        
        # Award certification achievement
        achievement = Achievement(
            user_id=user_id,
            achievement_type=AchievementType.CERTIFICATION,
            title=f"Certified: {course_title}",
            description=f"Completed {course_title} with {final_score}% score",
            icon_url="/achievements/certificate.png",
            criteria={"course_id": course_id, "score": final_score},
            course_id=course_id
        )
        
        self.achievements[user_id].append(achievement)
        
        return certificate
        
    async def get_course_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get personalized course recommendations"""
        # In production, use ML recommendation engine
        
        # Mock recommendations
        recommendations = [
            {
                "course_id": "course_001",
                "title": "Advanced Trading Strategies",
                "reason": "Based on your interest in investing",
                "match_score": 0.92
            },
            {
                "course_id": "course_002",
                "title": "Risk Management Fundamentals",
                "reason": "Recommended for your skill level",
                "match_score": 0.87
            },
            {
                "course_id": "course_003",
                "title": "Cryptocurrency Deep Dive",
                "reason": "Trending topic in your learning path",
                "match_score": 0.85
            }
        ]
        
        return recommendations[:limit]
        
    async def assess_skill_level(self, user_id: str) -> SkillLevel:
        """Assess user's current skill level"""
        # In production, analyze quiz scores, course completions, etc.
        
        # Mock assessment
        user_achievements = len(self.achievements.get(user_id, []))
        
        if user_achievements >= 20:
            return SkillLevel.EXPERT
        elif user_achievements >= 10:
            return SkillLevel.ADVANCED
        elif user_achievements >= 5:
            return SkillLevel.INTERMEDIATE
        else:
            return SkillLevel.BEGINNER
            
    async def get_user_goals(self, user_id: str) -> List[str]:
        """Get user's learning goals"""
        goals = self.user_goals.get(user_id, [])
        return [g.title for g in goals]
        
    async def get_user_interests(self, user_id: str) -> List[str]:
        """Get user's learning interests"""
        # In production, analyze from course enrollments and activity
        return ["investing", "portfolio management", "cryptocurrency"]
        
    async def assess_learning_goals(self, user_id: str) -> List[LearningGoal]:
        """Assess and suggest learning goals"""
        # In production, analyze user profile and behavior
        
        suggested_goals = [
            LearningGoal(
                title="Master Stock Market Basics",
                description="Understand fundamental stock market concepts",
                category="Investing",
                skill_level_target=SkillLevel.INTERMEDIATE,
                target_date=datetime.now() + timedelta(days=90),
                related_skills=["stock analysis", "market timing", "portfolio construction"]
            ),
            LearningGoal(
                title="Build Diversified Portfolio",
                description="Learn to create and manage a balanced investment portfolio",
                category="Portfolio Management",
                skill_level_target=SkillLevel.INTERMEDIATE,
                target_date=datetime.now() + timedelta(days=120),
                related_skills=["asset allocation", "risk management", "rebalancing"]
            )
        ]
        
        return suggested_goals
        
    async def _get_recommended_course_ids(
        self,
        user_id: str,
        goals: List[LearningGoal]
    ) -> List[str]:
        """Get recommended course IDs based on goals"""
        # In production, use recommendation engine
        
        # Mock recommendations based on goals
        recommendations = []
        
        for goal in goals:
            if "stock" in goal.title.lower():
                recommendations.append("course_stocks_101")
            if "portfolio" in goal.title.lower():
                recommendations.append("course_portfolio_mgmt")
            if "crypto" in goal.title.lower():
                recommendations.append("course_crypto_basics")
                
        return recommendations[:5]  # Limit to 5 recommendations
        
    async def get_active_learner_count(self) -> int:
        """Get count of active learners"""
        # In production, count users active in last 7 days
        return len(self.learning_paths)
        
    async def generate_learning_analytics(
        self,
        user_id: str
    ) -> LearningAnalytics:
        """Generate detailed learning analytics"""
        # In production, aggregate from various data sources
        
        # Mock analytics
        analytics = LearningAnalytics(
            user_id=user_id,
            total_courses_enrolled=3,
            total_courses_completed=1,
            current_streak_days=7,
            longest_streak_days=15,
            total_learning_hours=42.5,
            average_daily_minutes=35.2,
            most_active_hour=20,  # 8 PM
            most_active_day="Saturday",
            average_quiz_score=85.5,
            quiz_improvement_rate=0.15,
            preferred_lesson_types=["video", "interactive"],
            preferred_categories=["Investing", "Portfolio Management"],
            preferred_learning_time="evening",
            discussion_posts=12,
            helpful_votes_received=45,
            total_achievements=len(self.achievements.get(user_id, [])),
            total_certificates=len(self.certificates.get(user_id, [])),
            recommendation_click_rate=0.68,
            recommendation_completion_rate=0.45
        )
        
        return analytics 