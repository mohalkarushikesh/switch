# 🤖 Autonomous Trading System - Live Demo Guide

## Overview
The Oryza platform now features a **fully functional autonomous trading system** that demonstrates real AI-driven investment decisions.

---

## 🚀 Quick Start Demo

### 1. Start the Application
```bash
start_oryza.bat
```

### 2. Login
- Email: `test@oryza.com`
- Password: `test@123`

### 3. Navigate to Trading
Click "Trading" in the sidebar

---

## 📊 What You'll See

### Real-Time Market Simulation
- **Live Price Updates**: Stock prices change every second
- **Volume Fluctuations**: Realistic trading volume patterns
- **Market Events**: 
  - Random news impacts (1% chance/minute)
  - Earnings surprises (scheduled events)
  - Breakout patterns

### AI Agent Analysis (Updates Every 5 Seconds)

#### 1. **Equity Agent**
- Dynamic P/E ratio calculations
- Technical score (1-10) based on:
  - Moving average crossovers
  - Price vs MA20/MA50
  - RSI positioning
  - Breakout detection
- Shows "🚀 Breakout Detected!" when patterns emerge

#### 2. **Sentiment Agent**
- News sentiment changes with price movements
- Social score fluctuates (5-10)
- Shows "📅 Earnings Soon!" when approaching
- Market mood: Bullish/Neutral/Bearish

#### 3. **Risk Agent**
- Volatility assessment (Low/Medium/High)
- Dynamic beta calculation
- Real-time stop loss levels
- Position size recommendations

#### 4. **Timing Agent**
- Live RSI calculation (0-100)
- MACD signal detection
- Volume trend analysis
- Entry signals:
  - "Breakout - Enter Now"
  - "Oversold - Good Entry"
  - "Wait"

### AI Consensus
- **Background Color Changes**:
  - Green: STRONG_BUY (>75% confidence)
  - Blue: BUY (65-75% confidence)
  - Yellow: HOLD (50-65% confidence)
  - Red: AVOID (<50% confidence)
- **Trigger Badges**: Breakout, Earnings, Oversold, Momentum

---

## 🎮 Interactive Demo Steps

### Step 1: Watch Live Analysis
1. Select different stocks from the watchlist
2. Observe how agent analyses change
3. Notice consensus shifts with market conditions

### Step 2: Enable Autonomous Trading
1. Click the purple "Autonomous Trading" toggle
2. Set parameters:
   - Investment Amount: ₹100,000
   - Risk Tolerance: Moderate
   - Max Position Size: 5-7%
3. Click "Enable AI Trading"

### Step 3: Monitor Automatic Execution
- **What Happens**:
  1. AI continuously scans all stocks
  2. When consensus > 75%, creates orders
  3. Executes trades automatically
  4. Updates positions in real-time

### Step 4: View Active Positions
- Navigate to the positions section
- See:
  - Entry/current prices
  - Live P&L updates
  - Stop loss adjustments
  - AI recommendations

---

## 🔬 Behind the Scenes

### Market Simulator Features
```python
# Price generation with realistic patterns
- Gaussian random walk
- Trend components
- Intraday volatility patterns
- Event-driven price jumps
```

### Consensus Algorithm
```python
# Multi-agent scoring
- Equity: 0.2-0.9 based on technicals
- Sentiment: 0.3-0.8 based on market mood
- Risk: 0.4-0.8 (inverse of volatility)
- Timing: 0.2-0.95 based on entry signals
```

### Trading Logic
```python
# Autonomous execution
if consensus_score > 0.75:
    action = "STRONG_BUY"
    create_order()
elif consensus_score > 0.65:
    action = "BUY"
    evaluate_opportunity()
```

---

## 📈 Expected Behaviors

### During Normal Market Conditions
- Gradual price movements (±0.5-2%)
- Occasional buy signals
- Conservative position sizing

### During Breakouts
- Price breaks resistance levels
- Multiple agents turn bullish
- Immediate buy execution
- Larger position sizes

### During Earnings Events
- Sudden price jumps (±5-8%)
- High volatility warnings
- Adjusted position sizes
- Tighter stop losses

### Risk Management
- Dynamic stop loss adjustment
- Profit protection (moves stop to breakeven at +5%)
- Automatic position closure at targets
- Portfolio diversification enforcement

---

## 🎯 Key Differentiators

1. **Real AI Analysis**: Not static data - actual calculations
2. **Event-Driven**: Responds to simulated market events
3. **Multi-Agent Consensus**: Multiple perspectives combined
4. **Continuous Learning**: Performance tracking and optimization
5. **Risk-First Approach**: Protection mechanisms throughout

---

## 🛠️ Customization Options

### For Conservative Investors
- Set risk tolerance to "Conservative"
- Max position size: 3%
- Tighter stop losses

### For Growth Seekers
- Set risk tolerance to "Aggressive"
- Max position size: 10%
- Focus on momentum stocks

### For Balanced Approach
- Default "Moderate" settings
- 5-7% position sizing
- Mix of value and growth

---

## 📊 Performance Metrics

The system tracks:
- Win rate percentage
- Average return per trade
- Maximum drawdown
- Sharpe ratio equivalent
- Best/worst trades

---

## 🔔 Notifications You'll See

- "AI executed: Buy 25 shares of RELIANCE"
- "Stop loss adjusted to breakeven"
- "Take profit reached - position closed"
- "New breakout opportunity detected"

---

## ⚡ Live Demo Talking Points

1. **"Watch how the AI reacts to this breakout"**
   - Point out the technical score increase
   - Show consensus shift to STRONG_BUY
   - Demonstrate automatic execution

2. **"Notice the risk management in action"**
   - Show stop loss levels
   - Explain position sizing logic
   - Demonstrate profit protection

3. **"This is truly autonomous"**
   - No human intervention needed
   - 24/7 monitoring capability
   - Learns from outcomes

---

## 🚨 Important Notes

- This is a demonstration with simulated market data
- Real implementation would require:
  - Broker API integration
  - Regulatory compliance
  - Real market data feeds
  - Actual fund management
- The AI logic and decision-making framework is production-ready

---

*"Experience the future of investing - where AI doesn't just advise, it acts."* 