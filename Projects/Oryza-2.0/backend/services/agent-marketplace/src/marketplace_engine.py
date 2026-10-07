"""
AI Agent Marketplace - Platform for sharing and monetizing trading strategies
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

class StrategyStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    UNDER_REVIEW = "under_review"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class MarketplaceEngine:
    """
    Marketplace for AI trading agents and strategies
    """
    
    def __init__(self):
        self.strategies = {}
        self.subscriptions = {}
        self.ratings = {}
        self.transactions = {}
        self.performance_history = {}
        
        # Categories for strategies
        self.categories = [
            "Momentum Trading",
            "Mean Reversion",
            "Arbitrage",
            "Options Strategies",
            "ESG Focused",
            "Crypto Trading",
            "Multi-Asset",
            "High Frequency",
            "Value Investing",
            "Growth Investing"
        ]
        
        # Pricing tiers
        self.pricing_models = {
            "free": {"base_price": 0, "revenue_share": 0},
            "basic": {"base_price": 999, "revenue_share": 0.10},
            "premium": {"base_price": 4999, "revenue_share": 0.15},
            "professional": {"base_price": 9999, "revenue_share": 0.20},
            "enterprise": {"base_price": 49999, "revenue_share": 0.25}
        }
    
    async def create_strategy(
        self,
        creator_id: str,
        strategy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new trading strategy for the marketplace"""
        
        strategy_id = f"strat_{uuid.uuid4().hex[:12]}"
        
        # Validate strategy code
        validation = await self._validate_strategy(strategy_data)
        if not validation["valid"]:
            return {"error": validation["message"]}
        
        strategy = {
            "strategy_id": strategy_id,
            "creator_id": creator_id,
            "name": strategy_data["name"],
            "description": strategy_data["description"],
            "category": strategy_data["category"],
            "tags": strategy_data.get("tags", []),
            "pricing_model": strategy_data.get("pricing_model", "basic"),
            "price": self.pricing_models[strategy_data.get("pricing_model", "basic")]["base_price"],
            "status": StrategyStatus.DRAFT.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "requirements": strategy_data.get("requirements", {}),
            "performance": {
                "backtest_return": 0,
                "live_return": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "total_trades": 0
            },
            "statistics": {
                "subscribers": 0,
                "total_revenue": 0,
                "average_rating": 0,
                "total_ratings": 0,
                "downloads": 0
            },
            "code": {
                "language": strategy_data.get("language", "python"),
                "entry_point": strategy_data.get("entry_point", "main"),
                "dependencies": strategy_data.get("dependencies", []),
                "config_schema": strategy_data.get("config_schema", {})
            }
        }
        
        # Store strategy code securely
        strategy["code"]["encrypted_source"] = await self._encrypt_strategy_code(
            strategy_data.get("source_code", "")
        )
        
        self.strategies[strategy_id] = strategy
        self.ratings[strategy_id] = []
        self.performance_history[strategy_id] = []
        
        return {
            "strategy": strategy,
            "message": "Strategy created successfully. Submit for review to publish."
        }
    
    async def _validate_strategy(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate strategy before creation"""
        
        # Check required fields
        required_fields = ["name", "description", "category", "source_code"]
        for field in required_fields:
            if field not in strategy_data:
                return {
                    "valid": False,
                    "message": f"Missing required field: {field}"
                }
        
        # Validate category
        if strategy_data["category"] not in self.categories:
            return {
                "valid": False,
                "message": f"Invalid category. Choose from: {', '.join(self.categories)}"
            }
        
        # Basic code validation (in production, this would be more thorough)
        if len(strategy_data.get("source_code", "")) < 100:
            return {
                "valid": False,
                "message": "Strategy code too short. Please provide a complete implementation."
            }
        
        # Check for prohibited patterns (security)
        prohibited_patterns = ["eval(", "exec(", "__import__", "os.system"]
        code = strategy_data.get("source_code", "")
        for pattern in prohibited_patterns:
            if pattern in code:
                return {
                    "valid": False,
                    "message": f"Prohibited pattern detected: {pattern}"
                }
        
        return {"valid": True}
    
    async def _encrypt_strategy_code(self, source_code: str) -> str:
        """Encrypt strategy source code for storage"""
        # In production, use proper encryption
        # For demo, we'll use a simple encoding
        import base64
        return base64.b64encode(source_code.encode()).decode()
    
    async def submit_for_review(self, strategy_id: str, creator_id: str) -> Dict[str, Any]:
        """Submit strategy for marketplace review"""
        
        if strategy_id not in self.strategies:
            return {"error": "Strategy not found"}
        
        strategy = self.strategies[strategy_id]
        
        if strategy["creator_id"] != creator_id:
            return {"error": "Unauthorized"}
        
        if strategy["status"] != StrategyStatus.DRAFT.value:
            return {"error": "Strategy must be in draft status"}
        
        # Run automated tests
        test_results = await self._run_strategy_tests(strategy_id)
        
        if not test_results["passed"]:
            return {
                "error": "Strategy failed automated tests",
                "test_results": test_results
            }
        
        # Update status
        strategy["status"] = StrategyStatus.UNDER_REVIEW.value
        strategy["submitted_at"] = datetime.now().isoformat()
        
        # Simulate review process (in production, this would be manual/automated)
        asyncio.create_task(self._review_strategy(strategy_id))
        
        return {
            "message": "Strategy submitted for review. You'll be notified once approved.",
            "estimated_review_time": "24-48 hours"
        }
    
    async def _run_strategy_tests(self, strategy_id: str) -> Dict[str, Any]:
        """Run automated tests on strategy"""
        
        tests = {
            "syntax_check": True,
            "performance_test": True,
            "risk_assessment": True,
            "backtest_validation": True,
            "code_quality": True
        }
        
        # Simulate test results
        import random
        for test in tests:
            tests[test] = random.random() > 0.1  # 90% pass rate
        
        return {
            "passed": all(tests.values()),
            "details": tests,
            "score": sum(tests.values()) / len(tests) * 100
        }
    
    async def _review_strategy(self, strategy_id: str):
        """Simulate strategy review process"""
        await asyncio.sleep(5)  # Simulate review time
        
        strategy = self.strategies[strategy_id]
        
        # Simulate approval (90% approval rate)
        import random
        if random.random() > 0.1:
            strategy["status"] = StrategyStatus.PUBLISHED.value
            strategy["published_at"] = datetime.now().isoformat()
            
            # Generate initial performance metrics
            strategy["performance"] = {
                "backtest_return": random.uniform(5, 50),
                "sharpe_ratio": random.uniform(0.5, 2.5),
                "max_drawdown": random.uniform(-20, -5),
                "win_rate": random.uniform(40, 70),
                "total_trades": random.randint(100, 1000)
            }
        else:
            strategy["status"] = StrategyStatus.DRAFT.value
            strategy["review_notes"] = "Strategy needs improvements in risk management"
    
    async def browse_strategies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "popularity",
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Browse available strategies in the marketplace"""
        
        # Filter strategies
        filtered_strategies = []
        for strategy in self.strategies.values():
            if strategy["status"] != StrategyStatus.PUBLISHED.value:
                continue
            
            if filters:
                # Category filter
                if "category" in filters and strategy["category"] != filters["category"]:
                    continue
                
                # Price filter
                if "max_price" in filters and strategy["price"] > filters["max_price"]:
                    continue
                
                # Performance filter
                if "min_return" in filters:
                    if strategy["performance"]["backtest_return"] < filters["min_return"]:
                        continue
                
                # Rating filter
                if "min_rating" in filters:
                    if strategy["statistics"]["average_rating"] < filters["min_rating"]:
                        continue
            
            filtered_strategies.append(strategy)
        
        # Sort strategies
        if sort_by == "popularity":
            filtered_strategies.sort(
                key=lambda x: x["statistics"]["subscribers"], 
                reverse=True
            )
        elif sort_by == "performance":
            filtered_strategies.sort(
                key=lambda x: x["performance"]["backtest_return"], 
                reverse=True
            )
        elif sort_by == "rating":
            filtered_strategies.sort(
                key=lambda x: x["statistics"]["average_rating"], 
                reverse=True
            )
        elif sort_by == "price_low":
            filtered_strategies.sort(key=lambda x: x["price"])
        elif sort_by == "newest":
            filtered_strategies.sort(
                key=lambda x: x["published_at"], 
                reverse=True
            )
        
        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_strategies = filtered_strategies[start_idx:end_idx]
        
        return {
            "strategies": paginated_strategies,
            "total": len(filtered_strategies),
            "page": page,
            "limit": limit,
            "total_pages": (len(filtered_strategies) + limit - 1) // limit
        }
    
    async def subscribe_to_strategy(
        self,
        user_id: str,
        strategy_id: str,
        payment_method: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Subscribe to a strategy"""
        
        if strategy_id not in self.strategies:
            return {"error": "Strategy not found"}
        
        strategy = self.strategies[strategy_id]
        
        if strategy["status"] != StrategyStatus.PUBLISHED.value:
            return {"error": "Strategy not available"}
        
        # Check if already subscribed
        subscription_key = f"{user_id}:{strategy_id}"
        if subscription_key in self.subscriptions:
            if self.subscriptions[subscription_key]["status"] == "active":
                return {"error": "Already subscribed to this strategy"}
        
        # Process payment (simulated)
        payment_result = await self._process_payment(
            user_id, strategy["price"], payment_method
        )
        
        if not payment_result["success"]:
            return {"error": "Payment failed", "details": payment_result["message"]}
        
        # Create subscription
        subscription = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "strategy_id": strategy_id,
            "status": "active",
            "subscribed_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            "payment": {
                "amount": strategy["price"],
                "transaction_id": payment_result["transaction_id"],
                "revenue_share": self.pricing_models[strategy["pricing_model"]]["revenue_share"]
            }
        }
        
        self.subscriptions[subscription_key] = subscription
        
        # Update strategy statistics
        strategy["statistics"]["subscribers"] += 1
        strategy["statistics"]["downloads"] += 1
        strategy["statistics"]["total_revenue"] += strategy["price"]
        
        # Get strategy code for user
        strategy_code = await self._get_strategy_code(strategy_id)
        
        return {
            "subscription": subscription,
            "strategy_code": strategy_code,
            "message": "Successfully subscribed to strategy"
        }
    
    async def _process_payment(
        self,
        user_id: str,
        amount: float,
        payment_method: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment for strategy subscription"""
        
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
    
    async def _get_strategy_code(self, strategy_id: str) -> Dict[str, Any]:
        """Get decrypted strategy code for subscriber"""
        
        strategy = self.strategies[strategy_id]
        
        # Decrypt code (in production, use proper decryption)
        import base64
        source_code = base64.b64decode(
            strategy["code"]["encrypted_source"]
        ).decode()
        
        return {
            "language": strategy["code"]["language"],
            "source_code": source_code,
            "dependencies": strategy["code"]["dependencies"],
            "config_schema": strategy["code"]["config_schema"],
            "documentation": strategy.get("documentation", ""),
            "examples": strategy.get("examples", [])
        }
    
    async def rate_strategy(
        self,
        user_id: str,
        strategy_id: str,
        rating: int,
        review: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rate and review a strategy"""
        
        if strategy_id not in self.strategies:
            return {"error": "Strategy not found"}
        
        # Check if user is subscribed
        subscription_key = f"{user_id}:{strategy_id}"
        if subscription_key not in self.subscriptions:
            return {"error": "You must be subscribed to rate this strategy"}
        
        if not 1 <= rating <= 5:
            return {"error": "Rating must be between 1 and 5"}
        
        # Add rating
        rating_entry = {
            "user_id": user_id,
            "rating": rating,
            "review": review,
            "created_at": datetime.now().isoformat(),
            "helpful_count": 0
        }
        
        self.ratings[strategy_id].append(rating_entry)
        
        # Update strategy statistics
        strategy = self.strategies[strategy_id]
        all_ratings = [r["rating"] for r in self.ratings[strategy_id]]
        strategy["statistics"]["average_rating"] = sum(all_ratings) / len(all_ratings)
        strategy["statistics"]["total_ratings"] = len(all_ratings)
        
        return {
            "message": "Rating submitted successfully",
            "average_rating": strategy["statistics"]["average_rating"]
        }
    
    async def get_creator_dashboard(self, creator_id: str) -> Dict[str, Any]:
        """Get dashboard for strategy creators"""
        
        # Get creator's strategies
        my_strategies = [
            s for s in self.strategies.values() 
            if s["creator_id"] == creator_id
        ]
        
        # Calculate earnings
        total_earnings = sum(s["statistics"]["total_revenue"] for s in my_strategies)
        total_subscribers = sum(s["statistics"]["subscribers"] for s in my_strategies)
        
        # Performance metrics
        avg_rating = sum(
            s["statistics"]["average_rating"] * s["statistics"]["total_ratings"] 
            for s in my_strategies if s["statistics"]["total_ratings"] > 0
        ) / max(sum(s["statistics"]["total_ratings"] for s in my_strategies), 1)
        
        # Recent activity
        recent_subscriptions = []
        for strategy in my_strategies:
            strategy_subs = [
                sub for sub in self.subscriptions.values()
                if sub["strategy_id"] == strategy["strategy_id"]
            ]
            recent_subscriptions.extend(strategy_subs[-5:])
        
        recent_subscriptions.sort(key=lambda x: x["subscribed_at"], reverse=True)
        
        return {
            "strategies": my_strategies,
            "statistics": {
                "total_strategies": len(my_strategies),
                "published_strategies": len([s for s in my_strategies if s["status"] == "published"]),
                "total_earnings": total_earnings,
                "total_subscribers": total_subscribers,
                "average_rating": avg_rating
            },
            "recent_activity": {
                "subscriptions": recent_subscriptions[:10],
                "reviews": self._get_recent_reviews(creator_id)[:10]
            },
            "earnings_chart": self._generate_earnings_chart(creator_id)
        }
    
    def _get_recent_reviews(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get recent reviews for creator's strategies"""
        creator_strategies = [
            s["strategy_id"] for s in self.strategies.values()
            if s["creator_id"] == creator_id
        ]
        
        all_reviews = []
        for strategy_id in creator_strategies:
            strategy_reviews = [
                {**r, "strategy_id": strategy_id}
                for r in self.ratings.get(strategy_id, [])
                if r.get("review")
            ]
            all_reviews.extend(strategy_reviews)
        
        all_reviews.sort(key=lambda x: x["created_at"], reverse=True)
        return all_reviews
    
    def _generate_earnings_chart(self, creator_id: str) -> List[Dict[str, Any]]:
        """Generate earnings data for visualization"""
        # Simulate monthly earnings data
        earnings_data = []
        current_date = datetime.now()
        
        for i in range(12):
            month_date = current_date - timedelta(days=30 * i)
            earnings = sum(
                s["statistics"]["total_revenue"] / (i + 1)
                for s in self.strategies.values()
                if s["creator_id"] == creator_id
            )
            
            earnings_data.append({
                "month": month_date.strftime("%B %Y"),
                "earnings": earnings,
                "subscribers": int(earnings / 1000)  # Rough estimate
            })
        
        earnings_data.reverse()
        return earnings_data
    
    async def get_strategy_performance(
        self,
        strategy_id: str,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """Get detailed performance metrics for a strategy"""
        
        if strategy_id not in self.strategies:
            return {"error": "Strategy not found"}
        
        strategy = self.strategies[strategy_id]
        
        # Generate performance data
        performance_data = {
            "overview": strategy["performance"],
            "historical_returns": self._generate_return_series(strategy_id, timeframe),
            "trade_analysis": {
                "avg_trade_duration": "2.5 days",
                "avg_profit_per_trade": "₹2,450",
                "largest_win": "₹45,000",
                "largest_loss": "₹-12,000",
                "consecutive_wins": 8,
                "consecutive_losses": 3
            },
            "risk_metrics": {
                "value_at_risk": -8.5,
                "sortino_ratio": 1.8,
                "calmar_ratio": 2.1,
                "beta": 0.85,
                "alpha": 0.12
            },
            "comparison": {
                "vs_nifty": "+12.5%",
                "vs_category_avg": "+8.3%",
                "percentile_rank": 85
            }
        }
        
        return performance_data
    
    def _generate_return_series(self, strategy_id: str, timeframe: str) -> List[Dict[str, Any]]:
        """Generate historical return series"""
        import random
        
        days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365
        }.get(timeframe, 30)
        
        returns = []
        cumulative = 100
        
        for i in range(days):
            daily_return = random.gauss(0.1, 2)  # 0.1% mean, 2% std dev
            cumulative *= (1 + daily_return / 100)
            
            returns.append({
                "date": (datetime.now() - timedelta(days=days-i)).isoformat(),
                "return": daily_return,
                "cumulative": cumulative - 100
            })
        
        return returns 