"""
Content Library - Manages educational resources and materials
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from .models import (
    Resource, ResourceType, GlossaryTerm, Webinar,
    WebinarStatus, Discussion
)


class ContentLibrary:
    """
    Manages educational resources, glossary, webinars, and discussions
    """
    
    def __init__(self):
        self.logger = logging.getLogger("content_library")
        self.resources = {}  # resource_id -> Resource
        self.glossary = {}  # term_id -> GlossaryTerm
        self.webinars = {}  # webinar_id -> Webinar
        self.discussions = {}  # discussion_id -> Discussion
        self.webinar_registrations = defaultdict(set)  # webinar_id -> Set[user_id]
        self.discussion_threads = defaultdict(list)  # course_id -> List[discussion_id]
        
    async def initialize(self):
        """Initialize content library"""
        self.logger.info("Initializing Content Library")
        
        # In production:
        # - Load resources from storage
        # - Initialize search index
        # - Set up CDN for content delivery
        
        # Create sample content
        await self._create_sample_content()
        
    async def _create_sample_content(self):
        """Create sample content for testing"""
        # Sample Resources
        resources_data = [
            {
                "title": "Investment Strategy Template",
                "description": "Professional investment strategy documentation template",
                "resource_type": ResourceType.TEMPLATE,
                "category": "Portfolio Management",
                "tags": ["strategy", "portfolio", "planning"],
                "download_url": "/resources/investment-strategy-template.pdf",
                "file_size_mb": 2.5
            },
            {
                "title": "Compound Interest Calculator",
                "description": "Interactive calculator for compound interest projections",
                "resource_type": ResourceType.CALCULATOR,
                "category": "Financial Planning",
                "tags": ["calculator", "compound interest", "planning"],
                "download_url": "/resources/compound-calculator.xlsx",
                "file_size_mb": 0.5
            },
            {
                "title": "Complete Guide to ETFs",
                "description": "Comprehensive ebook on Exchange-Traded Funds",
                "resource_type": ResourceType.EBOOK,
                "category": "Investment Products",
                "tags": ["ETF", "guide", "investing"],
                "download_url": "/resources/etf-guide.pdf",
                "file_size_mb": 8.2,
                "author": "Dr. Sarah Chen"
            },
            {
                "title": "Risk Assessment Checklist",
                "description": "Step-by-step checklist for investment risk assessment",
                "resource_type": ResourceType.CHECKLIST,
                "category": "Risk Management",
                "tags": ["risk", "checklist", "assessment"],
                "download_url": "/resources/risk-checklist.pdf",
                "file_size_mb": 0.8
            },
            {
                "title": "Market Cycles Infographic",
                "description": "Visual guide to understanding market cycles",
                "resource_type": ResourceType.INFOGRAPHIC,
                "category": "Market Analysis",
                "tags": ["market cycles", "infographic", "analysis"],
                "preview_url": "/resources/market-cycles-preview.jpg",
                "download_url": "/resources/market-cycles.pdf",
                "file_size_mb": 3.5
            }
        ]
        
        for res_data in resources_data:
            resource = Resource(**res_data)
            self.resources[resource.resource_id] = resource
            
        # Sample Glossary Terms
        glossary_data = [
            {
                "term": "P/E Ratio",
                "aliases": ["Price-to-Earnings Ratio", "PE"],
                "definition": "A valuation ratio calculated by dividing market price per share by earnings per share",
                "extended_definition": "The P/E ratio indicates how much investors are willing to pay per dollar of earnings. A high P/E might indicate overvaluation or high growth expectations.",
                "examples": ["If a stock trades at $100 and has EPS of $5, its P/E ratio is 20"],
                "category": "Valuation Metrics",
                "related_terms": ["EPS", "PEG Ratio", "Valuation"]
            },
            {
                "term": "Diversification",
                "definition": "Investment strategy of spreading risk across different assets",
                "extended_definition": "Diversification reduces portfolio risk by investing in assets that react differently to market conditions. It's based on the principle of not putting all eggs in one basket.",
                "examples": ["A diversified portfolio might include stocks, bonds, real estate, and commodities"],
                "category": "Portfolio Management",
                "related_terms": ["Asset Allocation", "Risk Management", "Correlation"]
            },
            {
                "term": "Compound Interest",
                "definition": "Interest calculated on the initial principal and accumulated interest",
                "extended_definition": "Compound interest accelerates wealth growth by earning returns on both the original investment and previously earned interest. Einstein called it the 'eighth wonder of the world'.",
                "examples": ["$1,000 at 10% annual compound interest becomes $1,610 after 5 years"],
                "category": "Basic Concepts",
                "related_terms": ["Simple Interest", "APY", "Time Value of Money"]
            },
            {
                "term": "Market Cap",
                "aliases": ["Market Capitalization"],
                "definition": "Total market value of a company's outstanding shares",
                "extended_definition": "Market cap is calculated by multiplying the current stock price by the total number of outstanding shares. It's used to categorize companies as large-cap, mid-cap, or small-cap.",
                "examples": ["A company with 1 million shares at $50/share has a market cap of $50 million"],
                "category": "Company Analysis",
                "related_terms": ["Enterprise Value", "Float", "Outstanding Shares"]
            }
        ]
        
        for term_data in glossary_data:
            term = GlossaryTerm(**term_data)
            self.glossary[term.term_id] = term
            
        # Sample Webinars
        webinars_data = [
            {
                "title": "Advanced Options Strategies",
                "description": "Learn complex options strategies for income and hedging",
                "topic": "Options Trading",
                "instructor_name": "Michael Zhang, CFA",
                "instructor_bio": "20+ years derivatives trading experience",
                "scheduled_at": datetime.now() + timedelta(days=7),
                "duration_minutes": 90,
                "max_attendees": 500,
                "status": WebinarStatus.SCHEDULED
            },
            {
                "title": "Crypto Portfolio Management",
                "description": "Best practices for managing digital asset portfolios",
                "topic": "Cryptocurrency",
                "instructor_name": "Alex Kumar",
                "instructor_bio": "Blockchain expert and fund manager",
                "scheduled_at": datetime.now() + timedelta(days=14),
                "duration_minutes": 60,
                "status": WebinarStatus.SCHEDULED
            },
            {
                "title": "Tax-Efficient Investing",
                "description": "Strategies to minimize tax impact on investments",
                "topic": "Tax Planning",
                "instructor_name": "Lisa Wang, CPA",
                "instructor_bio": "Tax specialist for high-net-worth individuals",
                "scheduled_at": datetime.now() - timedelta(days=7),
                "duration_minutes": 75,
                "status": WebinarStatus.COMPLETED,
                "recording_url": "/webinars/tax-efficient-investing-recording.mp4"
            }
        ]
        
        for webinar_data in webinars_data:
            webinar = Webinar(**webinar_data)
            self.webinars[webinar.webinar_id] = webinar
            
    async def get_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Resource]:
        """Get resources with filters"""
        resources = list(self.resources.values())
        
        # Filter by type
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
            
        # Filter by category
        if category:
            resources = [r for r in resources if r.category == category]
            
        # Search
        if search:
            search_lower = search.lower()
            resources = [
                r for r in resources
                if search_lower in r.title.lower() or
                search_lower in r.description.lower() or
                any(search_lower in tag for tag in r.tags)
            ]
            
        # Sort by download count (popularity)
        resources.sort(key=lambda r: r.download_count, reverse=True)
        
        # Pagination
        return resources[offset:offset + limit]
        
    async def search_glossary(
        self,
        term: str,
        limit: int = 10
    ) -> List[GlossaryTerm]:
        """Search glossary terms"""
        results = []
        term_lower = term.lower()
        
        for glossary_term in self.glossary.values():
            score = 0
            
            # Exact term match
            if term_lower == glossary_term.term.lower():
                score += 10
            # Term contains search
            elif term_lower in glossary_term.term.lower():
                score += 5
            # Alias match
            elif any(term_lower in alias.lower() for alias in glossary_term.aliases):
                score += 4
            # Definition contains term
            elif term_lower in glossary_term.definition.lower():
                score += 2
            # Related terms
            elif any(term_lower in related.lower() for related in glossary_term.related_terms):
                score += 1
                
            if score > 0:
                results.append((score, glossary_term))
                
        # Sort by relevance
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [term for _, term in results[:limit]]
        
    async def get_glossary_term(self, term_id: str) -> Optional[GlossaryTerm]:
        """Get glossary term by ID"""
        return self.glossary.get(term_id)
        
    async def get_webinars(
        self,
        status: Optional[WebinarStatus] = None,
        upcoming_only: bool = True
    ) -> List[Webinar]:
        """Get webinars"""
        webinars = list(self.webinars.values())
        
        # Filter by status
        if status:
            webinars = [w for w in webinars if w.status == status]
            
        # Filter upcoming
        if upcoming_only:
            now = datetime.now()
            webinars = [w for w in webinars if w.scheduled_at > now]
            
        # Sort by schedule
        webinars.sort(key=lambda w: w.scheduled_at)
        
        return webinars
        
    async def register_for_webinar(
        self,
        user_id: str,
        webinar_id: str
    ) -> Dict[str, Any]:
        """Register user for webinar"""
        webinar = self.webinars.get(webinar_id)
        if not webinar:
            raise ValueError(f"Webinar {webinar_id} not found")
            
        if webinar.status != WebinarStatus.SCHEDULED:
            raise ValueError("Cannot register for past or cancelled webinars")
            
        # Check capacity
        if webinar.max_attendees:
            current_registrations = len(self.webinar_registrations[webinar_id])
            if current_registrations >= webinar.max_attendees:
                raise ValueError("Webinar is full")
                
        # Register user
        self.webinar_registrations[webinar_id].add(user_id)
        webinar.registered_count = len(self.webinar_registrations[webinar_id])
        
        return {
            "webinar_id": webinar_id,
            "user_id": user_id,
            "registered_at": datetime.now(),
            "webinar_details": {
                "title": webinar.title,
                "scheduled_at": webinar.scheduled_at,
                "meeting_url": webinar.meeting_url  # Would be sent via email
            }
        }
        
    async def get_discussions(
        self,
        course_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Discussion]:
        """Get course discussions"""
        discussion_ids = self.discussion_threads.get(course_id, [])
        
        discussions = []
        for disc_id in discussion_ids:
            discussion = self.discussions.get(disc_id)
            if discussion:
                discussions.append(discussion)
                
        # Sort by activity (last reply or creation)
        discussions.sort(
            key=lambda d: d.last_reply_at or d.created_at,
            reverse=True
        )
        
        # Apply pagination
        return discussions[offset:offset + limit]
        
    async def create_discussion(
        self,
        user_id: str,
        course_id: str,
        title: str,
        content: str
    ) -> Discussion:
        """Create a new discussion thread"""
        discussion = Discussion(
            course_id=course_id,
            user_id=user_id,
            title=title,
            content=content,
            author_name=f"User_{user_id[-4:]}",  # Would fetch from user service
        )
        
        # Store discussion
        self.discussions[discussion.discussion_id] = discussion
        self.discussion_threads[course_id].append(discussion.discussion_id)
        
        self.logger.info(f"Created discussion {discussion.discussion_id} in course {course_id}")
        
        return discussion
        
    async def reply_to_discussion(
        self,
        discussion_id: str,
        user_id: str,
        content: str
    ) -> Dict[str, Any]:
        """Reply to a discussion thread"""
        discussion = self.discussions.get(discussion_id)
        if not discussion:
            raise ValueError(f"Discussion {discussion_id} not found")
            
        # In production, store replies separately
        # For now, just update counts
        discussion.reply_count += 1
        discussion.last_reply_at = datetime.now()
        discussion.updated_at = datetime.now()
        
        reply = {
            "reply_id": f"reply_{datetime.now().timestamp()}",
            "discussion_id": discussion_id,
            "user_id": user_id,
            "content": content,
            "created_at": datetime.now()
        }
        
        return reply
        
    async def like_discussion(
        self,
        discussion_id: str,
        user_id: str
    ) -> bool:
        """Like a discussion"""
        discussion = self.discussions.get(discussion_id)
        if not discussion:
            return False
            
        # In production, track individual likes
        discussion.like_count += 1
        
        return True
        
    async def mark_discussion_resolved(
        self,
        discussion_id: str,
        user_id: str
    ) -> bool:
        """Mark discussion as resolved"""
        discussion = self.discussions.get(discussion_id)
        if not discussion:
            return False
            
        # Check if user is author or instructor
        if discussion.user_id != user_id:  # In production, also check instructor status
            return False
            
        discussion.is_resolved = True
        discussion.updated_at = datetime.now()
        
        return True
        
    async def get_resource_categories(self) -> List[str]:
        """Get all resource categories"""
        categories = set(r.category for r in self.resources.values())
        return sorted(list(categories))
        
    async def get_popular_resources(self, limit: int = 10) -> List[Resource]:
        """Get most popular resources"""
        resources = list(self.resources.values())
        resources.sort(key=lambda r: r.download_count, reverse=True)
        return resources[:limit]
        
    async def track_resource_download(
        self,
        resource_id: str,
        user_id: str
    ):
        """Track resource download"""
        resource = self.resources.get(resource_id)
        if resource:
            resource.download_count += 1
            
    async def get_upcoming_webinar_count(self) -> int:
        """Get count of upcoming webinars"""
        now = datetime.now()
        return sum(
            1 for w in self.webinars.values()
            if w.scheduled_at > now and w.status == WebinarStatus.SCHEDULED
        )
        
    async def search_all_content(
        self,
        query: str,
        limit: int = 20
    ) -> Dict[str, List[Any]]:
        """Search across all content types"""
        results = {
            "resources": [],
            "glossary": [],
            "webinars": [],
            "discussions": []
        }
        
        query_lower = query.lower()
        
        # Search resources
        for resource in self.resources.values():
            if (query_lower in resource.title.lower() or
                query_lower in resource.description.lower()):
                results["resources"].append(resource)
                
        # Search glossary
        results["glossary"] = await self.search_glossary(query, limit=5)
        
        # Search webinars
        for webinar in self.webinars.values():
            if (query_lower in webinar.title.lower() or
                query_lower in webinar.description.lower()):
                results["webinars"].append(webinar)
                
        # Search discussions
        for discussion in self.discussions.values():
            if (query_lower in discussion.title.lower() or
                query_lower in discussion.content.lower()):
                results["discussions"].append(discussion)
                
        # Limit results
        for key in results:
            results[key] = results[key][:limit]
            
        return results 