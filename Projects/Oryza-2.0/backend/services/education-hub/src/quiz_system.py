"""
Quiz System - Manages quizzes, questions, and grading
"""
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import random

from .models import (
    Quiz, QuizQuestion, QuizAttempt, QuizType, SkillLevel
)


class QuizSystem:
    """
    Manages educational quizzes and assessments
    """
    
    def __init__(self):
        self.logger = logging.getLogger("quiz_system")
        self.quizzes = {}  # quiz_id -> Quiz
        self.questions = {}  # quiz_id -> List[QuizQuestion]
        self.attempts = {}  # attempt_id -> QuizAttempt
        self.user_attempts = {}  # (user_id, quiz_id) -> List[attempt_id]
        
    async def initialize(self):
        """Initialize quiz system"""
        self.logger.info("Initializing Quiz System")
        
        # In production:
        # - Load quiz templates
        # - Initialize grading engine
        # - Set up analytics
        
        # Create sample quizzes
        await self._create_sample_quizzes()
        
    async def _create_sample_quizzes(self):
        """Create sample quizzes for testing"""
        # Investment Basics Quiz
        basics_quiz = Quiz(
            quiz_id="quiz_inv_basics",
            course_id="course_basics",
            module_id="module_1",
            title="Investment Fundamentals Quiz",
            description="Test your understanding of basic investment concepts",
            instructions="Select the best answer for each question. You have 30 minutes to complete this quiz.",
            question_count=10,
            passing_score=70.0,
            time_limit_minutes=30,
            difficulty_level=SkillLevel.BEGINNER
        )
        self.quizzes[basics_quiz.quiz_id] = basics_quiz
        
        # Create questions for basics quiz
        basics_questions = [
            QuizQuestion(
                quiz_id=basics_quiz.quiz_id,
                question_type=QuizType.MULTIPLE_CHOICE,
                question_text="What is compound interest?",
                options=[
                    {"id": "a", "text": "Interest paid only on the principal amount"},
                    {"id": "b", "text": "Interest paid on both principal and accumulated interest"},
                    {"id": "c", "text": "A type of bank account"},
                    {"id": "d", "text": "A government bond"}
                ],
                correct_answer="b",
                explanation="Compound interest is interest calculated on both the initial principal and the accumulated interest from previous periods.",
                points=1,
                order=1
            ),
            QuizQuestion(
                quiz_id=basics_quiz.quiz_id,
                question_type=QuizType.TRUE_FALSE,
                question_text="Diversification helps reduce investment risk.",
                options=[
                    {"id": "true", "text": "True"},
                    {"id": "false", "text": "False"}
                ],
                correct_answer="true",
                explanation="Diversification spreads risk across different investments, reducing the impact of any single investment's poor performance.",
                points=1,
                order=2
            ),
            QuizQuestion(
                quiz_id=basics_quiz.quiz_id,
                question_type=QuizType.MULTIPLE_CHOICE,
                question_text="Which of the following is typically considered the riskiest investment?",
                options=[
                    {"id": "a", "text": "Government bonds"},
                    {"id": "b", "text": "Blue-chip stocks"},
                    {"id": "c", "text": "Cryptocurrency"},
                    {"id": "d", "text": "Savings account"}
                ],
                correct_answer="c",
                explanation="Cryptocurrencies are highly volatile and speculative, making them typically the riskiest among these options.",
                points=1,
                order=3
            )
        ]
        
        self.questions[basics_quiz.quiz_id] = basics_questions
        
        # Portfolio Management Quiz
        portfolio_quiz = Quiz(
            quiz_id="quiz_portfolio_mgmt",
            course_id="course_portfolio",
            title="Portfolio Management Assessment",
            description="Evaluate your portfolio management knowledge",
            question_count=15,
            passing_score=75.0,
            time_limit_minutes=45,
            difficulty_level=SkillLevel.INTERMEDIATE
        )
        self.quizzes[portfolio_quiz.quiz_id] = portfolio_quiz
        
    async def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID"""
        return self.quizzes.get(quiz_id)
        
    async def get_quiz_questions(
        self,
        quiz_id: str,
        hide_answers: bool = False
    ) -> List[QuizQuestion]:
        """Get questions for a quiz"""
        questions = self.questions.get(quiz_id, [])
        
        if hide_answers:
            # Return questions without correct answers
            sanitized_questions = []
            for q in questions:
                q_copy = q.copy()
                q_copy.correct_answer = None
                q_copy.explanation = None
                sanitized_questions.append(q_copy)
            return sanitized_questions
            
        return questions
        
    async def can_access_quiz(
        self,
        user_id: str,
        quiz_id: str
    ) -> bool:
        """Check if user can access quiz"""
        # In production, check enrollment and prerequisites
        return True
        
    async def can_attempt_quiz(
        self,
        user_id: str,
        quiz_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Check if user can attempt quiz"""
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return False, "Quiz not found"
            
        # Check attempt limit
        user_attempt_ids = self.user_attempts.get((user_id, quiz_id), [])
        if quiz.max_attempts and len(user_attempt_ids) >= quiz.max_attempts:
            return False, f"Maximum attempts ({quiz.max_attempts}) reached"
            
        # Check if there's an incomplete attempt
        for attempt_id in user_attempt_ids:
            attempt = self.attempts.get(attempt_id)
            if attempt and not attempt.is_completed:
                return False, "You have an incomplete attempt"
                
        return True, None
        
    async def create_attempt(
        self,
        user_id: str,
        quiz_id: str
    ) -> QuizAttempt:
        """Create a new quiz attempt"""
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")
            
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id
        )
        
        self.attempts[attempt.attempt_id] = attempt
        
        # Track user attempts
        key = (user_id, quiz_id)
        if key not in self.user_attempts:
            self.user_attempts[key] = []
        self.user_attempts[key].append(attempt.attempt_id)
        
        self.logger.info(f"Created attempt {attempt.attempt_id} for user {user_id}")
        
        return attempt
        
    async def get_attempt(self, attempt_id: str) -> Optional[QuizAttempt]:
        """Get attempt by ID"""
        return self.attempts.get(attempt_id)
        
    async def get_user_attempts(
        self,
        user_id: str,
        quiz_id: str
    ) -> List[QuizAttempt]:
        """Get user's attempts for a quiz"""
        attempt_ids = self.user_attempts.get((user_id, quiz_id), [])
        
        attempts = []
        for attempt_id in attempt_ids:
            attempt = self.attempts.get(attempt_id)
            if attempt:
                attempts.append(attempt)
                
        # Sort by start time
        attempts.sort(key=lambda a: a.started_at, reverse=True)
        
        return attempts
        
    async def grade_quiz(
        self,
        attempt_id: str,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Grade quiz attempt"""
        attempt = self.attempts.get(attempt_id)
        if not attempt:
            raise ValueError(f"Attempt {attempt_id} not found")
            
        quiz = self.quizzes.get(attempt.quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {attempt.quiz_id} not found")
            
        questions = self.questions.get(attempt.quiz_id, [])
        
        # Grade each answer
        total_points = 0
        earned_points = 0
        question_results = []
        
        # Convert answers list to dict for easier lookup
        answer_map = {a["question_id"]: a["answer"] for a in answers}
        
        for question in questions:
            total_points += question.points
            
            user_answer = answer_map.get(question.question_id)
            is_correct = False
            points_earned = 0
            
            if user_answer is not None:
                if question.question_type == QuizType.MULTIPLE_CHOICE:
                    is_correct = user_answer == question.correct_answer
                elif question.question_type == QuizType.TRUE_FALSE:
                    is_correct = str(user_answer).lower() == str(question.correct_answer).lower()
                elif question.question_type == QuizType.FILL_BLANK:
                    # Case-insensitive comparison for fill-in-the-blank
                    is_correct = str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
                    
                if is_correct:
                    points_earned = question.points
                elif question.partial_credit:
                    # In production, implement partial credit logic
                    points_earned = question.points * 0.5
                    
            earned_points += points_earned
            
            question_results.append({
                "question_id": question.question_id,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "points_earned": points_earned,
                "explanation": question.explanation if quiz.show_explanations else None
            })
            
        # Calculate score
        score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = score_percentage >= quiz.passing_score
        
        # Update attempt
        attempt.completed_at = datetime.now()
        attempt.time_spent_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())
        attempt.answers = answer_map
        attempt.score = score_percentage
        attempt.passed = passed
        attempt.is_completed = True
        
        result = {
            "attempt_id": attempt_id,
            "score": score_percentage,
            "passed": passed,
            "total_points": total_points,
            "earned_points": earned_points,
            "passing_score": quiz.passing_score,
            "time_spent_seconds": attempt.time_spent_seconds,
            "question_results": question_results if quiz.show_correct_answers else None
        }
        
        # Issue certificate if passed and it's a course completion quiz
        if passed and quiz.course_id:
            # In production, check if this completes the course
            pass
            
        self.logger.info(f"Graded attempt {attempt_id}: {score_percentage:.1f}%")
        
        return result
        
    async def create_quiz(
        self,
        title: str,
        description: str,
        course_id: Optional[str] = None,
        module_id: Optional[str] = None,
        questions: List[Dict[str, Any]] = None
    ) -> Quiz:
        """Create a new quiz"""
        quiz = Quiz(
            title=title,
            description=description,
            course_id=course_id,
            module_id=module_id,
            question_count=len(questions) if questions else 0
        )
        
        self.quizzes[quiz.quiz_id] = quiz
        
        # Create questions if provided
        if questions:
            quiz_questions = []
            for i, q_data in enumerate(questions):
                question = QuizQuestion(
                    quiz_id=quiz.quiz_id,
                    question_type=QuizType(q_data["type"]),
                    question_text=q_data["text"],
                    options=q_data.get("options"),
                    correct_answer=q_data["answer"],
                    explanation=q_data.get("explanation"),
                    points=q_data.get("points", 1),
                    order=i + 1
                )
                quiz_questions.append(question)
                
            self.questions[quiz.quiz_id] = quiz_questions
            
        return quiz
        
    async def generate_practice_quiz(
        self,
        topic: str,
        difficulty: SkillLevel,
        question_count: int = 10
    ) -> Quiz:
        """Generate a practice quiz on a topic"""
        # In production, use AI to generate questions
        
        quiz = Quiz(
            title=f"Practice Quiz: {topic}",
            description=f"Test your knowledge of {topic}",
            question_count=question_count,
            passing_score=0.0,  # No pass/fail for practice
            max_attempts=None,  # Unlimited attempts
            difficulty_level=difficulty,
            show_correct_answers=True,
            show_explanations=True
        )
        
        self.quizzes[quiz.quiz_id] = quiz
        
        # Generate sample questions
        # In production, this would use AI or question bank
        self.questions[quiz.quiz_id] = []
        
        return quiz
        
    async def get_quiz_statistics(
        self,
        quiz_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a quiz"""
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            return {}
            
        # Gather all attempts
        all_attempts = []
        for (user_id, qid), attempt_ids in self.user_attempts.items():
            if qid == quiz_id:
                for attempt_id in attempt_ids:
                    attempt = self.attempts.get(attempt_id)
                    if attempt and attempt.is_completed:
                        all_attempts.append(attempt)
                        
        if not all_attempts:
            return {
                "total_attempts": 0,
                "average_score": 0,
                "pass_rate": 0
            }
            
        # Calculate statistics
        scores = [a.score for a in all_attempts if a.score is not None]
        passed = [a for a in all_attempts if a.passed]
        
        stats = {
            "total_attempts": len(all_attempts),
            "unique_users": len(set(a.user_id for a in all_attempts)),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "pass_rate": len(passed) / len(all_attempts) * 100 if all_attempts else 0,
            "average_time_seconds": sum(a.time_spent_seconds or 0 for a in all_attempts) / len(all_attempts),
            "difficulty_rating": self._calculate_difficulty_rating(scores)
        }
        
        return stats
        
    def _calculate_difficulty_rating(self, scores: List[float]) -> str:
        """Calculate difficulty rating based on scores"""
        if not scores:
            return "Unknown"
            
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 85:
            return "Easy"
        elif avg_score >= 70:
            return "Moderate"
        elif avg_score >= 55:
            return "Challenging"
        else:
            return "Difficult"
            
    async def get_question_analytics(
        self,
        quiz_id: str
    ) -> List[Dict[str, Any]]:
        """Get analytics for each question"""
        questions = self.questions.get(quiz_id, [])
        if not questions:
            return []
            
        # Analyze each question
        analytics = []
        
        for question in questions:
            # Count correct/incorrect answers
            correct_count = 0
            total_count = 0
            
            # In production, analyze from all attempts
            # Mock data for now
            analytics.append({
                "question_id": question.question_id,
                "question_text": question.question_text[:50] + "...",
                "correct_rate": 0.75,  # Mock 75% correct rate
                "average_time_seconds": 45,
                "difficulty_index": 0.25,  # 0-1, lower is easier
                "discrimination_index": 0.6  # How well it distinguishes good students
            })
            
        return analytics 