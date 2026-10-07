start application 
	frontend
		cd /frontend
		npm start  
	backend 
		cd backend\services\api-gateway
		python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

Login with any credentials: dummy
Email: test@oryza.com (or any email)
Password: test@123



(venv) PS C:\Users\2327238\Documents\devlopment\ai\projects\Oryza\frontend> npm start

> oryza-frontend@1.0.0 start
> react-scripts start

'react-scripts' is not recognized as an internal or external command,
operable program or batch file.

solution => 

	```
	rmdir node_modules folder 
	del package-lock.json
	npm cache clean --force
	npm install (install again dependeciess)  : once check with cursor

	If that doesn't work, install react-scripts directly
		npm install react-scripts --save
		npm start

	else try 
		npx react-scripts start
		
	```

# Install all dependencies (including react-scripts)
	npm install --legacy-peer-deps

# After installation completes, start the frontend
	npm start

- Frontend: Fully functional with all pages (Dashboard, Trading, GOALS, Profile, ANALYTICS, NEWS, Notifications, Settings)
- Databases: Complete setup with schemas and seed data
- Auth Service: Production-ready authentication at port 8001
- WebSocket Service: Real-time updates at port 8002

🔧 To Install Docker (Optional):
If you want to use Docker later, you can:
Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
Install and restart your computer
Then use: docker compose -f docker-compose.demo.yml up --build

💡 What I've Done:
Created start_demo_simple.bat - Runs the test API and frontend
Created start_all_services.bat - Runs all microservices (for later when you need full functionality)

Frontend: http://localhost:3000
Backend API: http://localhost:8889

# One command to rule them all:
docker-compose -f docker-compose.demo.yml up --build

🏗️ What's STRUCTURED but NOT Implemented:
	AI/ML Features
		Multi-agent system (only folder structure exists)
		FinBERT sentiment analysis (not integrated)
		ESG scoring (service folder only)
		Behavioral prediction (not active)
		Autonomous trading (not implemented)
		Advanced Features from Prompt
		Wealth concierge (no actual automation)
		Bill negotiation (not built)
		Tax optimization (not implemented)
		Voice UI (not added)
		AR visualization (not included)

❌ What's NOT Implemented at All:
	Actual AI models
	Multi-agent negotiation
	Real broker integration
	Payment gateway
	Multiple databases (only mock data)
	Advanced security features
	International markets
	Cryptocurrency trading

## run the project 

# Start everything
./start_oryza.bat

# Initialize demo data
python backend/initialize_demo_data.py

# Access platform
# Frontend: http://localhost:3000
# Backend: http://localhost:8889
# Login: test@example.com / test123