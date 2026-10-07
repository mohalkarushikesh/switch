# Oryza Demo Checklist

## 🔍 Features to Test

### ✅ Authentication
- [ ] Login with test@oryza.com / test@123
- [ ] Logout functionality
- [ ] Session persistence (refresh page)
- [ ] Protected routes redirect to login

### ✅ Dashboard
- [ ] Portfolio summary cards display
- [ ] Market overview section
- [ ] Recent transactions list
- [ ] Quick stats (Total Value, Today's Change, etc.)

### ✅ Trading Interface
- [ ] View order book
- [ ] Place buy/sell orders
- [ ] View order history
- [ ] Real-time price updates (mock)

### ✅ Goals Page
- [ ] Create financial goals
- [ ] Track goal progress
- [ ] View goal timeline
- [ ] Edit/Delete goals

### ✅ Analytics Page
- [ ] Portfolio performance charts
- [ ] Asset allocation pie chart
- [ ] Historical performance
- [ ] Risk metrics

### ✅ News Page
- [ ] News feed display
- [ ] Filter by category
- [ ] Sentiment indicators
- [ ] Market impact predictions

### ✅ Profile Page
- [ ] View user information
- [ ] Edit profile details
- [ ] Risk preference settings
- [ ] Account settings

### ✅ UI/UX
- [ ] Responsive design (test on mobile view)
- [ ] Navigation works smoothly
- [ ] No UI gaps or overlaps
- [ ] Loading states
- [ ] Error handling

## 🐛 Known Issues to Document
1. Backend services require manual startup without Docker
2. Data is mock/static (not connected to real databases)
3. WebSocket real-time updates are simulated

## 📝 Demo Flow Script
1. Start with login screen - show modern UI
2. Dashboard - highlight key metrics and clean layout
3. Navigate to Trading - show order placement
4. Go to Goals - demonstrate financial planning
5. Show Analytics - portfolio performance
6. Check News - market sentiment analysis
7. End with Profile - personalization features 