"""
AI Voice Assistant & Chatbot - Natural language interface for the platform
"""
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import re

class IntentType(Enum):
    PORTFOLIO_QUERY = "portfolio_query"
    MARKET_INFO = "market_info"
    TRADE_EXECUTION = "trade_execution"
    GOAL_PLANNING = "goal_planning"
    EDUCATION = "education"
    GENERAL_HELP = "general_help"
    RISK_ANALYSIS = "risk_analysis"
    ESG_QUERY = "esg_query"
    TAX_QUERY = "tax_query"
    SUBSCRIPTION = "subscription"

class ConversationContext:
    def __init__(self):
        self.user_id = None
        self.session_id = None
        self.history = []
        self.current_intent = None
        self.entities = {}
        self.pending_action = None

class VoiceChatbot:
    """
    AI-powered voice assistant and chatbot for natural language interactions
    """
    
    def __init__(self):
        self.sessions = {}
        self.intent_patterns = self._initialize_intent_patterns()
        self.responses = self._initialize_responses()
        self.voice_enabled = True
        
        # NLP components
        self.entity_extractors = {
            "stock_symbol": r"\b([A-Z]{2,10})\b",
            "amount": r"₹?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|lac|k|thousand|crore|cr)?",
            "percentage": r"(\d+(?:\.\d+)?)\s*%",
            "time_period": r"(\d+)\s*(day|week|month|year)s?",
            "order_type": r"\b(buy|sell|purchase|sold)\b"
        }
        
        # Voice synthesis settings
        self.voice_settings = {
            "language": "en-IN",
            "speed": 1.0,
            "pitch": 1.0,
            "voice_id": "oryza_assistant"
        }
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize intent recognition patterns"""
        return {
            IntentType.PORTFOLIO_QUERY: [
                r"show.*portfolio",
                r"what.*my.*holdings",
                r"how.*investments.*doing",
                r"portfolio.*value",
                r"current.*positions",
                r"profit.*loss"
            ],
            IntentType.MARKET_INFO: [
                r"market.*today",
                r"how.*\b[A-Z]{2,10}\b.*doing",
                r"price.*\b[A-Z]{2,10}\b",
                r"stock.*quote",
                r"market.*news",
                r"top.*gainers"
            ],
            IntentType.TRADE_EXECUTION: [
                r"buy.*shares?",
                r"sell.*stocks?",
                r"place.*order",
                r"execute.*trade",
                r"purchase.*\b[A-Z]{2,10}\b"
            ],
            IntentType.GOAL_PLANNING: [
                r"retirement.*plan",
                r"save.*for",
                r"financial.*goal",
                r"how.*much.*need",
                r"target.*amount"
            ],
            IntentType.RISK_ANALYSIS: [
                r"risk.*portfolio",
                r"am.*i.*risky",
                r"diversified",
                r"portfolio.*safe",
                r"risk.*score"
            ],
            IntentType.ESG_QUERY: [
                r"esg.*score",
                r"sustainable.*investment",
                r"green.*stocks",
                r"environmental.*impact",
                r"social.*responsibility"
            ],
            IntentType.EDUCATION: [
                r"learn.*about",
                r"what.*is.*\w+",
                r"explain.*\w+",
                r"course.*on",
                r"teach.*me"
            ],
            IntentType.TAX_QUERY: [
                r"tax.*saving",
                r"capital.*gains",
                r"tax.*harvesting",
                r"elss",
                r"80c.*deduction"
            ]
        }
    
    def _initialize_responses(self) -> Dict[str, List[str]]:
        """Initialize response templates"""
        return {
            "greeting": [
                "Hello! I'm your Oryza AI assistant. How can I help you with your investments today?",
                "Welcome back! Ready to check your portfolio or explore new opportunities?",
                "Hi there! I'm here to help with all your investment needs."
            ],
            "clarification": [
                "I'm not sure I understood that. Could you rephrase?",
                "Let me make sure I got that right. You want to {intent}?",
                "Could you provide more details about what you'd like to do?"
            ],
            "confirmation": [
                "Got it! I'll {action} right away.",
                "Sure, let me {action} for you.",
                "Understood. Processing your request to {action}."
            ],
            "error": [
                "I encountered an issue: {error}. Would you like to try again?",
                "Sorry, I couldn't complete that action. {error}",
                "There was a problem: {error}. How else can I help?"
            ]
        }
    
    async def start_session(self, user_id: str, voice_enabled: bool = True) -> Dict[str, Any]:
        """Start a new conversation session"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        context = ConversationContext()
        context.user_id = user_id
        context.session_id = session_id
        
        self.sessions[session_id] = context
        self.voice_enabled = voice_enabled
        
        # Get user's name from profile
        user_name = await self._get_user_name(user_id)
        
        greeting = f"Hello {user_name}! " if user_name else "Hello! "
        greeting += "I'm your Oryza AI assistant. You can ask me about your portfolio, market updates, place trades, or explore investment opportunities. How can I help you today?"
        
        response = {
            "session_id": session_id,
            "message": greeting,
            "voice_enabled": voice_enabled,
            "suggestions": [
                "Show my portfolio",
                "How is RELIANCE doing?",
                "Buy 10 shares of TCS",
                "What's my risk score?",
                "Find ESG investments"
            ]
        }
        
        if voice_enabled:
            response["audio_url"] = await self._synthesize_speech(greeting)
        
        return response
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        voice_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user message and generate response"""
        
        if session_id not in self.sessions:
            return {"error": "Invalid session"}
        
        context = self.sessions[session_id]
        
        # Add to conversation history
        context.history.append({
            "role": "user",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # If voice input provided, use speech-to-text
        if voice_input:
            message = await self._transcribe_speech(voice_input)
        
        # Extract intent and entities
        intent, entities = await self._understand_message(message, context)
        context.current_intent = intent
        context.entities = entities
        
        # Generate response based on intent
        response_data = await self._handle_intent(intent, entities, context)
        
        # Add to conversation history
        context.history.append({
            "role": "assistant",
            "message": response_data["message"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate voice response if enabled
        if self.voice_enabled and "message" in response_data:
            response_data["audio_url"] = await self._synthesize_speech(response_data["message"])
        
        return response_data
    
    async def _understand_message(
        self,
        message: str,
        context: ConversationContext
    ) -> Tuple[IntentType, Dict[str, Any]]:
        """Understand user intent and extract entities"""
        
        message_lower = message.lower()
        intent = None
        confidence = 0
        
        # Match against intent patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    intent = intent_type
                    confidence = 0.8
                    break
            if intent:
                break
        
        # Default to general help if no match
        if not intent:
            intent = IntentType.GENERAL_HELP
            confidence = 0.3
        
        # Extract entities
        entities = {}
        
        # Extract stock symbols
        stock_matches = re.findall(self.entity_extractors["stock_symbol"], message)
        if stock_matches:
            entities["stocks"] = stock_matches
        
        # Extract amounts
        amount_matches = re.findall(self.entity_extractors["amount"], message_lower)
        if amount_matches:
            amounts = []
            for match in amount_matches:
                amount = float(match.replace(",", ""))
                if "lakh" in message_lower or "lac" in message_lower:
                    amount *= 100000
                elif "crore" in message_lower or "cr" in message_lower:
                    amount *= 10000000
                elif "k" in message_lower or "thousand" in message_lower:
                    amount *= 1000
                amounts.append(amount)
            entities["amounts"] = amounts
        
        # Extract order type
        order_matches = re.findall(self.entity_extractors["order_type"], message_lower)
        if order_matches:
            entities["order_type"] = order_matches[0]
        
        # Extract percentages
        percentage_matches = re.findall(self.entity_extractors["percentage"], message)
        if percentage_matches:
            entities["percentages"] = [float(p) for p in percentage_matches]
        
        # Extract time periods
        time_matches = re.findall(self.entity_extractors["time_period"], message_lower)
        if time_matches:
            entities["time_periods"] = [(int(num), unit) for num, unit in time_matches]
        
        # Extract quantities
        quantity_pattern = r"(\d+)\s*(?:shares?|units?|stocks?)"
        quantity_matches = re.findall(quantity_pattern, message_lower)
        if quantity_matches:
            entities["quantities"] = [int(q) for q in quantity_matches]
        
        return intent, entities
    
    async def _handle_intent(
        self,
        intent: IntentType,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle user intent and generate appropriate response"""
        
        if intent == IntentType.PORTFOLIO_QUERY:
            return await self._handle_portfolio_query(entities, context)
        
        elif intent == IntentType.MARKET_INFO:
            return await self._handle_market_info(entities, context)
        
        elif intent == IntentType.TRADE_EXECUTION:
            return await self._handle_trade_execution(entities, context)
        
        elif intent == IntentType.GOAL_PLANNING:
            return await self._handle_goal_planning(entities, context)
        
        elif intent == IntentType.RISK_ANALYSIS:
            return await self._handle_risk_analysis(entities, context)
        
        elif intent == IntentType.ESG_QUERY:
            return await self._handle_esg_query(entities, context)
        
        elif intent == IntentType.EDUCATION:
            return await self._handle_education_query(entities, context)
        
        elif intent == IntentType.TAX_QUERY:
            return await self._handle_tax_query(entities, context)
        
        else:
            return await self._handle_general_help(entities, context)
    
    async def _handle_portfolio_query(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle portfolio-related queries"""
        
        # Fetch portfolio data (mock)
        portfolio = {
            "total_value": 1250000,
            "total_gain": 125000,
            "total_gain_percent": 11.11,
            "top_holdings": [
                {"symbol": "RELIANCE", "value": 125000, "gain_percent": 8.5},
                {"symbol": "TCS", "value": 87000, "gain_percent": 12.3},
                {"symbol": "HDFC", "value": 65000, "gain_percent": -2.1}
            ]
        }
        
        message = f"Your portfolio is worth ₹{portfolio['total_value']:,.0f}, "
        message += f"with a total gain of ₹{portfolio['total_gain']:,.0f} ({portfolio['total_gain_percent']:.1f}%). "
        message += "\n\nTop holdings:\n"
        
        for holding in portfolio["top_holdings"]:
            gain_text = "up" if holding["gain_percent"] > 0 else "down"
            message += f"• {holding['symbol']}: ₹{holding['value']:,.0f} ({gain_text} {abs(holding['gain_percent']):.1f}%)\n"
        
        return {
            "message": message,
            "data": portfolio,
            "chart_url": "https://cdn.oryza.ai/portfolio-chart.png",
            "actions": [
                {"label": "View Details", "action": "view_portfolio"},
                {"label": "Rebalance", "action": "rebalance_portfolio"}
            ]
        }
    
    async def _handle_market_info(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle market information queries"""
        
        stocks = entities.get("stocks", [])
        
        if stocks:
            # Get specific stock info
            stock = stocks[0]
            stock_data = {
                "symbol": stock,
                "price": 2456.50,
                "change": 23.45,
                "change_percent": 0.96,
                "day_high": 2485.00,
                "day_low": 2425.00,
                "volume": 1234567
            }
            
            message = f"{stock} is currently trading at ₹{stock_data['price']:,.2f}, "
            message += f"up ₹{stock_data['change']:.2f} ({stock_data['change_percent']:.2f}%) for the day. "
            message += f"Day's range: ₹{stock_data['day_low']:,.2f} - ₹{stock_data['day_high']:,.2f}"
            
            return {
                "message": message,
                "data": stock_data,
                "chart_url": f"https://cdn.oryza.ai/charts/{stock}.png",
                "actions": [
                    {"label": "Buy", "action": f"buy_{stock}"},
                    {"label": "Sell", "action": f"sell_{stock}"},
                    {"label": "Set Alert", "action": f"alert_{stock}"}
                ]
            }
        else:
            # General market overview
            market_data = {
                "nifty": {"value": 19845.50, "change": 125.30, "change_percent": 0.63},
                "sensex": {"value": 65782.30, "change": 412.45, "change_percent": 0.63}
            }
            
            message = "Market Update:\n"
            message += f"• NIFTY: {market_data['nifty']['value']:,.2f} "
            message += f"(+{market_data['nifty']['change']:.2f}, +{market_data['nifty']['change_percent']:.2f}%)\n"
            message += f"• SENSEX: {market_data['sensex']['value']:,.2f} "
            message += f"(+{market_data['sensex']['change']:.2f}, +{market_data['sensex']['change_percent']:.2f}%)\n"
            message += "\nMarkets are trading in the green today with positive global cues."
            
            return {
                "message": message,
                "data": market_data,
                "suggestions": ["Top gainers", "Top losers", "Sector performance"]
            }
    
    async def _handle_trade_execution(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle trade execution requests"""
        
        stocks = entities.get("stocks", [])
        quantities = entities.get("quantities", [])
        order_type = entities.get("order_type", "buy")
        
        if not stocks:
            return {
                "message": "Which stock would you like to trade? Please specify the symbol.",
                "awaiting_input": "stock_symbol"
            }
        
        if not quantities:
            return {
                "message": f"How many shares of {stocks[0]} would you like to {order_type}?",
                "awaiting_input": "quantity"
            }
        
        # Set pending action for confirmation
        context.pending_action = {
            "type": "trade",
            "stock": stocks[0],
            "quantity": quantities[0],
            "order_type": order_type,
            "price": 2456.50  # Mock current price
        }
        
        total_value = context.pending_action["quantity"] * context.pending_action["price"]
        
        message = f"Please confirm your order:\n"
        message += f"• {order_type.upper()} {context.pending_action['quantity']} shares of {context.pending_action['stock']}\n"
        message += f"• Current price: ₹{context.pending_action['price']:,.2f}\n"
        message += f"• Total value: ₹{total_value:,.2f}\n"
        message += "\nReply 'yes' to confirm or 'no' to cancel."
        
        return {
            "message": message,
            "pending_confirmation": True,
            "actions": [
                {"label": "Confirm", "action": "confirm_trade"},
                {"label": "Cancel", "action": "cancel_trade"},
                {"label": "Modify", "action": "modify_trade"}
            ]
        }
    
    async def _handle_risk_analysis(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle risk analysis queries"""
        
        risk_data = {
            "overall_score": 42.5,
            "risk_level": "Moderate",
            "breakdown": {
                "concentration": 35.2,
                "volatility": 48.3,
                "liquidity": 28.7,
                "correlation": 32.1,
                "market_conditions": 45.0
            },
            "recommendations": [
                "Portfolio is moderately concentrated. Consider diversifying across more sectors.",
                "Add defensive assets to reduce volatility.",
                "Current allocation aligns with your moderate risk profile."
            ]
        }
        
        message = f"Your portfolio risk score is {risk_data['overall_score']:.1f} ({risk_data['risk_level']})\n\n"
        message += "Risk Breakdown:\n"
        
        for factor, score in risk_data["breakdown"].items():
            message += f"• {factor.replace('_', ' ').title()}: {score:.1f}\n"
        
        message += "\nRecommendations:\n"
        for rec in risk_data["recommendations"]:
            message += f"• {rec}\n"
        
        return {
            "message": message,
            "data": risk_data,
            "visual_type": "risk_gauge",
            "actions": [
                {"label": "Reduce Risk", "action": "reduce_risk"},
                {"label": "View Details", "action": "risk_details"}
            ]
        }
    
    async def _handle_esg_query(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle ESG-related queries"""
        
        stocks = entities.get("stocks", [])
        
        if stocks:
            # Specific stock ESG score
            stock = stocks[0]
            esg_data = {
                "symbol": stock,
                "overall_score": 73.8,
                "rating": "AA",
                "breakdown": {
                    "environmental": 75.2,
                    "social": 71.5,
                    "governance": 74.6
                }
            }
            
            message = f"{stock} has an ESG score of {esg_data['overall_score']:.1f} (Rating: {esg_data['rating']})\n\n"
            message += "ESG Breakdown:\n"
            message += f"• Environmental: {esg_data['breakdown']['environmental']:.1f}\n"
            message += f"• Social: {esg_data['breakdown']['social']:.1f}\n"
            message += f"• Governance: {esg_data['breakdown']['governance']:.1f}\n"
            message += "\nThis company demonstrates strong sustainability practices."
            
        else:
            # Portfolio ESG overview
            message = "Your portfolio has an overall ESG score of 71.5 (AA rating)\n\n"
            message += "Top ESG holdings:\n"
            message += "• TCS: AAA rating (85.2 score)\n"
            message += "• WIPRO: AA rating (78.5 score)\n"
            message += "• ADANIGREEN: A rating (72.3 score)\n\n"
            message += "Consider our ESG-focused portfolios for sustainable investing."
        
        return {
            "message": message,
            "suggestions": ["View ESG portfolios", "Find green stocks", "Impact report"]
        }
    
    async def _handle_education_query(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle educational queries"""
        
        # Extract topic from message
        last_message = context.history[-1]["message"] if context.history else ""
        
        if "options" in last_message.lower():
            topic = "options trading"
            explanation = """Options are financial contracts that give you the right (but not obligation) to buy or sell a stock at a specific price before a certain date.

Key concepts:
• Call Option: Right to buy at a fixed price
• Put Option: Right to sell at a fixed price
• Strike Price: The fixed price in the contract
• Premium: The cost of buying the option
• Expiry Date: When the option expires

Options can be used for hedging risk or speculating on price movements. They're more complex than stocks, so I recommend our Options Trading course to learn more."""
            
        elif "pe ratio" in last_message.lower() or "p/e" in last_message.lower():
            topic = "P/E ratio"
            explanation = """The Price-to-Earnings (P/E) ratio is a valuation metric that compares a company's stock price to its earnings per share.

P/E Ratio = Stock Price ÷ Earnings Per Share

What it tells you:
• High P/E (>25): Stock may be overvalued or investors expect high growth
• Low P/E (<15): Stock may be undervalued or company has challenges
• Industry average P/E varies by sector

Example: If a stock trades at ₹100 and has EPS of ₹5, its P/E is 20."""
            
        else:
            topic = "investing basics"
            explanation = """I can help you learn about various investment topics! Here are some popular areas:

• Stock market basics
• Mutual funds and ETFs
• Technical analysis
• Fundamental analysis
• Risk management
• Portfolio diversification

Would you like me to explain any specific topic? You can also explore our comprehensive courses for structured learning."""
        
        return {
            "message": explanation,
            "related_courses": [
                "Introduction to Investing",
                "Technical Analysis Masterclass",
                "Value Investing Strategies"
            ],
            "actions": [
                {"label": "Browse Courses", "action": "view_courses"},
                {"label": "Start Learning", "action": "start_course"}
            ]
        }
    
    async def _handle_goal_planning(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle financial goal planning queries"""
        
        amounts = entities.get("amounts", [])
        time_periods = entities.get("time_periods", [])
        
        if not amounts:
            return {
                "message": "Let's plan your financial goal! How much money do you want to save?",
                "awaiting_input": "target_amount"
            }
        
        if not time_periods:
            return {
                "message": f"Great! You want to save ₹{amounts[0]:,.0f}. In how many years do you want to achieve this?",
                "awaiting_input": "time_period"
            }
        
        # Calculate required monthly investment
        target = amounts[0]
        years = time_periods[0][0] if time_periods[0][1] == "year" else time_periods[0][0] / 12
        
        # Assuming 12% annual return
        monthly_investment = self._calculate_sip(target, years, 0.12)
        
        message = f"To accumulate ₹{target:,.0f} in {years:.0f} years:\n\n"
        message += f"• Required monthly SIP: ₹{monthly_investment:,.0f}\n"
        message += f"• Expected annual return: 12%\n"
        message += f"• Total investment: ₹{monthly_investment * years * 12:,.0f}\n"
        message += f"• Expected gains: ₹{target - (monthly_investment * years * 12):,.0f}\n\n"
        message += "I can help you set up an automated investment plan. Would you like to proceed?"
        
        return {
            "message": message,
            "goal_data": {
                "target_amount": target,
                "time_years": years,
                "monthly_sip": monthly_investment
            },
            "actions": [
                {"label": "Start SIP", "action": "start_sip"},
                {"label": "Adjust Goal", "action": "modify_goal"},
                {"label": "View Options", "action": "investment_options"}
            ]
        }
    
    async def _handle_tax_query(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle tax-related queries"""
        
        message = "Here are some tax-saving investment options:\n\n"
        message += "Section 80C (₹1.5 lakh limit):\n"
        message += "• ELSS Mutual Funds - 3 year lock-in, potential for high returns\n"
        message += "• PPF - 15 year lock-in, 7.1% tax-free returns\n"
        message += "• Tax-saving FDs - 5 year lock-in\n"
        message += "• Life Insurance Premium\n\n"
        message += "Section 80D:\n"
        message += "• Health Insurance Premium - Up to ₹25,000\n\n"
        message += "Your current tax-saving investments: ₹85,000\n"
        message += "Remaining 80C limit: ₹65,000\n\n"
        message += "Would you like me to suggest a tax-saving portfolio?"
        
        return {
            "message": message,
            "tax_savings_potential": 46800,  # Assuming 30% tax bracket
            "actions": [
                {"label": "Invest in ELSS", "action": "invest_elss"},
                {"label": "Tax Calculator", "action": "tax_calculator"},
                {"label": "View All Options", "action": "tax_options"}
            ]
        }
    
    async def _handle_general_help(
        self,
        entities: Dict[str, Any],
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle general help queries"""
        
        message = "I can help you with:\n\n"
        message += "📊 **Portfolio Management**\n"
        message += "• Check portfolio value and performance\n"
        message += "• View holdings and P&L\n"
        message += "• Get rebalancing suggestions\n\n"
        message += "📈 **Trading**\n"
        message += "• Get real-time stock quotes\n"
        message += "• Place buy/sell orders\n"
        message += "• Set price alerts\n\n"
        message += "🎯 **Financial Planning**\n"
        message += "• Set and track goals\n"
        message += "• Calculate required investments\n"
        message += "• Plan for retirement\n\n"
        message += "🌱 **ESG Investing**\n"
        message += "• Check ESG scores\n"
        message += "• Find sustainable investments\n\n"
        message += "🎓 **Learning**\n"
        message += "• Investment concepts\n"
        message += "• Market analysis\n"
        message += "• Trading strategies\n\n"
        message += "Just ask me anything!"
        
        return {
            "message": message,
            "quick_actions": [
                "Show portfolio",
                "Market update",
                "Buy stocks",
                "Risk analysis",
                "Tax saving"
            ]
        }
    
    def _calculate_sip(self, target: float, years: float, annual_return: float) -> float:
        """Calculate required monthly SIP amount"""
        monthly_rate = annual_return / 12
        months = int(years * 12)
        
        if monthly_rate == 0:
            return target / months
        
        # SIP formula
        factor = ((1 + monthly_rate) ** months - 1) / monthly_rate
        monthly_investment = target / (factor * (1 + monthly_rate))
        
        return round(monthly_investment, -2)  # Round to nearest 100
    
    async def _get_user_name(self, user_id: str) -> Optional[str]:
        """Get user's name from profile"""
        # In production, this would fetch from user service
        return "Amit"  # Mock name
    
    async def _synthesize_speech(self, text: str) -> str:
        """Convert text to speech"""
        # In production, this would use TTS service
        # Return mock audio URL
        return f"https://cdn.oryza.ai/audio/{uuid.uuid4().hex[:8]}.mp3"
    
    async def _transcribe_speech(self, audio_data: str) -> str:
        """Convert speech to text"""
        # In production, this would use STT service
        # Return mock transcription
        return "Show me my portfolio"
    
    async def process_confirmation(
        self,
        session_id: str,
        confirmed: bool
    ) -> Dict[str, Any]:
        """Process confirmation for pending actions"""
        
        if session_id not in self.sessions:
            return {"error": "Invalid session"}
        
        context = self.sessions[session_id]
        
        if not context.pending_action:
            return {"message": "No pending action to confirm."}
        
        if confirmed:
            action = context.pending_action
            
            if action["type"] == "trade":
                # Execute trade
                message = f"✅ Order executed successfully!\n\n"
                message += f"{action['order_type'].upper()} {action['quantity']} shares of {action['stock']} "
                message += f"at ₹{action['price']:,.2f}\n"
                message += f"Order ID: ORD{uuid.uuid4().hex[:8].upper()}"
                
                response = {
                    "message": message,
                    "trade_confirmation": {
                        "order_id": f"ORD{uuid.uuid4().hex[:8].upper()}",
                        "status": "executed"
                    }
                }
            else:
                response = {"message": "Action confirmed and processed."}
        else:
            response = {"message": "Order cancelled. How else can I help you?"}
        
        # Clear pending action
        context.pending_action = None
        
        return response
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End conversation session"""
        
        if session_id in self.sessions:
            context = self.sessions[session_id]
            
            # Generate session summary
            summary = {
                "session_id": session_id,
                "duration": len(context.history),
                "intents_handled": list(set(
                    h.get("intent", "general") 
                    for h in context.history if h["role"] == "assistant"
                )),
                "actions_completed": []  # Would track completed actions
            }
            
            # Clean up session
            del self.sessions[session_id]
            
            return {
                "message": "Thank you for using Oryza AI Assistant. Have a great day!",
                "session_summary": summary
            }
        
        return {"message": "Session already ended."} 