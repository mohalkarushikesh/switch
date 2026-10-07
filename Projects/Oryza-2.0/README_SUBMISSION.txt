ORYZA PLATFORM - AI-Powered Wealth Management Solution
======================================================

Team: [Your Team Name]
Contact: [Your Email/Phone]

PROJECT OVERVIEW
----------------
Oryza is a comprehensive wealth management platform designed specifically for the Indian market.
It combines traditional trading with modern AI-powered advisory services, making investment
accessible and intelligent for all users.

PREREQUISITES
-------------
- Python 3.8 or higher
- Node.js 14 or higher
- Git
- Modern web browser (Chrome, Firefox, Edge)

QUICK START GUIDE (SIMPLE DEMO)
-------------------------------
We provide a simple demo setup that doesn't require Docker or complex installations.

Step 1: Backend Setup
   Open Command Prompt/Terminal:
   cd backend
   python -m venv venv
   venv\Scripts\activate     (Windows)
   source venv/bin/activate  (Mac/Linux)
   pip install -r requirements.txt
   python test_api_for_frontend.py

   The backend will start on http://localhost:8889

Step 2: Frontend Setup
   Open a NEW Command Prompt/Terminal:
   cd frontend
   npm install
   npm start

   The frontend will start on http://localhost:3000

Step 3: Login Credentials
   Email: test@oryza.com
   Password: test@123

KEY FEATURES TO DEMO
--------------------
1. Authentication System
   - Secure login/logout
   - User profile management

2. Dashboard
   - Portfolio overview
   - Market summary
   - Recent transactions

3. Trading Interface
   - Real-time stock prices
   - Buy/Sell orders
   - Order history
   - Export functionality

4. Portfolio Management
   - View holdings
   - Track P&L
   - Performance analytics

5. Financial Goals
   - Set investment goals
   - Track progress
   - AI recommendations

6. Market Intelligence
   - Live market data
   - News integration
   - Sentiment analysis

7. Analytics & Reports
   - Performance charts
   - Export reports
   - Historical data

TECHNOLOGY STACK
----------------
Frontend:
- React 18 with TypeScript
- Redux for state management
- Tailwind CSS for styling
- Chart.js for visualizations
- WebSocket for real-time updates

Backend:
- FastAPI (Python)
- Microservices architecture
- JWT authentication
- Mock data for demo

AI/ML Components (Conceptualized):
- Portfolio optimization
- Risk assessment
- Market prediction
- Personalized recommendations

ARCHITECTURE HIGHLIGHTS
-----------------------
- Microservices design for scalability
- Real-time updates via WebSocket
- RESTful API design
- Responsive UI/UX
- Security-first approach

TROUBLESHOOTING
---------------
1. Port Already in Use:
   - Kill processes on ports 8889 and 3000
   - Windows: netstat -ano | findstr :8889
   - Then: taskkill /F /PID [process_id]

2. Module Not Found:
   - Ensure virtual environment is activated
   - Run pip install -r requirements.txt again

3. Network Error on Login:
   - Ensure backend is running on port 8889
   - Check browser console for errors

FUTURE ROADMAP
--------------
- Real broker API integration
- Mobile application
- Advanced AI advisory
- International markets
- Cryptocurrency trading

EVALUATION NOTES
----------------
This project demonstrates:
✓ Full-stack development expertise
✓ Modern architecture patterns
✓ Financial domain knowledge
✓ AI/ML integration readiness
✓ Production-grade code quality

Thank you for reviewing Oryza Platform!
For any queries, contact: [Your Contact Info] 