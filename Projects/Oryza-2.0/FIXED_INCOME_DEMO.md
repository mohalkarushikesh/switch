# 🏦 Fixed Income Securities - Autonomous Management Demo

## Overview
The Oryza platform now features **comprehensive fixed income management** with yield curve tracking, ladder construction, credit event detection, and duration adjustment.

---

## 🚀 Features Implemented

### 1. **Multi-Agent Bond Analysis**
- **Fixed Income Agent**: YTM calculation, fair value assessment, liquidity scoring
- **Credit Agent**: Rating monitoring, spread analysis, downgrade risk detection
- **Duration Agent**: Rate sensitivity, convexity analysis, hedging recommendations
- **Yield Agent**: Curve positioning, carry & roll analysis, reinvestment risk

### 2. **Yield Curve Monitoring**
- Real-time yield curve updates
- Shape detection (Normal/Inverted/Flat)
- Rate environment assessment
- Strategy recommendations based on curve

### 3. **Bond Ladder Construction**
- Three strategies: Conservative, Moderate, Aggressive
- Automatic maturity spacing
- Rollover management
- Income optimization

### 4. **Duration Management**
- Automatic adjustment for rate changes
- Target duration based on market conditions
- Convexity optimization
- Interest rate hedging suggestions

---

## 📊 Bond Universe

### Government Securities
- **GOI 2Y**: 6.5% coupon, AAA rated
- **GOI 5Y**: 7.2% coupon, AAA rated
- **GOI 10Y**: 7.8% coupon, AAA rated

### Corporate Bonds
- **HDFC 3Y**: 8.2% coupon, AAA rated
- **ICICI 5Y**: 8.5% coupon, AAA rated
- **Tata Steel 7Y**: 9.2% coupon, AA rated

### Specialized Bonds
- **NHAI Tax-Free 15Y**: 7.0% tax-free coupon
- **SBI Perpetual**: 9.5% coupon, callable

---

## 🎮 Demo Walkthrough

### Step 1: View Bond Portfolio
1. Navigate to Trading → Fixed Income Securities
2. See current holdings with live pricing
3. View yield curve and maturity distribution
4. Check accrued interest and YTM

### Step 2: Enable AI Management
1. Click "Enable AI Management" button
2. System monitors:
   - Yield curve shifts every 30 seconds
   - Credit events in real-time
   - Maturity rollovers automatically

### Step 3: Multi-Agent Analysis
1. Click any bond for detailed analysis
2. Four specialized agents provide insights:
   - **Fixed Income**: "Undervalued by ₹2.50"
   - **Credit**: "AAA stable, spreads widening"
   - **Duration**: "Reduce duration in rising rates"
   - **Yield**: "Carry 1.5%, Roll 0.8%"

### Step 4: Bond Ladder Construction
1. Go to Ladder tab
2. Select investment amount and strategy
3. System automatically selects bonds
4. Creates maturity schedule
5. Manages rollovers automatically

---

## 🤖 How It Works

### Yield Curve Updates
```
Every 30 seconds:
1. Simulate curve shifts (±10 bps)
2. Update all bond prices using duration
3. Apply convexity adjustments
4. Recalculate spreads
```

### Credit Event Detection
- Monitors for downgrades
- Detects spread widening
- Triggers automatic switches
- Maintains credit quality

### Duration Adjustment
```
If rates rising + duration > target:
  → Find shorter duration bond
  → Same credit quality
  → Execute switch
  → Log adjustment
```

### Ladder Management
```
30 days before maturity:
  → Find replacement bond
  → Match original duration
  → Maintain ladder structure
  → Execute rollover
```

---

## 📈 Expected Behaviors

### Rising Rate Environment
- Duration targets shorten to 3 years
- Ladder focuses on short end
- Credit spreads widen
- Floating rate preference

### Falling Rate Environment
- Duration extends to 7 years
- Lock in higher yields
- Credit spreads tighten
- Fixed rate preference

### Credit Events
- Immediate detection
- Automatic quality upgrade
- Minimal yield give-up
- Risk mitigation

---

## 💡 Key Differentiators

1. **Real Yield Curve Tracking**
   - Not static data - live curve simulation
   - Realistic shifts and twists
   - Intraday volatility patterns

2. **Intelligent Ladder Construction**
   - Multiple spacing strategies
   - Automatic rebalancing
   - Tax-efficient placement

3. **Credit Event Response**
   - Proactive downgrades avoidance
   - Spread-based triggers
   - Quality preservation

4. **Duration Optimization**
   - Dynamic targeting
   - Convexity consideration
   - Hedge recommendations

---

## 🎯 Demo Scenarios

### Scenario 1: Rate Hike
1. Yield curve shifts up 25 bps
2. Long duration bonds fall 2-3%
3. AI shortens portfolio duration
4. Switches to 2-3 year bonds
5. Preserves capital

### Scenario 2: Credit Downgrade
1. Corporate bond downgraded to AA-
2. Spreads widen 50 bps
3. AI detects deterioration
4. Switches to AAA alternative
5. Maintains yield profile

### Scenario 3: Ladder Rollover
1. 2Y bond matures in 25 days
2. AI identifies replacement
3. Similar yield, same duration
4. Executes rollover
5. Ladder structure intact

---

## 📊 Visual Indicators

### Portfolio Summary
- Total Value with P&L
- Annual Income calculation
- Average Duration display
- Rate sensitivity meter

### Yield Curve Chart
- Live curve visualization
- Shape identification
- Historical comparison
- Strategy overlay

### Bond Cards
- Rating badges (AAA/AA/A)
- Type indicators (Govt/Corp/Tax-Free)
- Maturity countdown
- Yield changes

### Agent Analysis
- 🟢 Buy signals
- 🟡 Hold recommendations
- 🔴 Sell alerts
- Confidence percentages

---

## 🔔 Notifications

- "Duration adjusted from 5.2 to 3.8 years"
- "Credit event: Switched TATA to HDFC"
- "Ladder rollover: GOI 2Y → GOI 3Y"
- "Yield curve inverted - strategy updated"

---

## 🛠️ Strategies Available

### Conservative Ladder
- 5 rungs, 5-year maximum
- Government bonds only
- Equal spacing
- Capital preservation focus

### Moderate Ladder
- 7 rungs, 10-year maximum
- Mix of Govt and AAA Corp
- Equal spacing
- Balanced approach

### Aggressive Ladder
- 10 rungs, 15-year maximum
- Include AA bonds
- Barbell structure
- Yield maximization

---

## 📈 Performance Metrics

The system tracks:
- Total return (price + coupon)
- Duration-adjusted returns
- Credit migration impact
- Rollover efficiency
- Tax optimization (for tax-free bonds)

---

## ⚡ Live Demo Points

1. **"Watch yields update in real-time"**
   - Point to changing prices
   - Show duration impact
   - Explain convexity benefit

2. **"See credit spreads in action"**
   - Government vs Corporate
   - Spread trends
   - Quality premium

3. **"Ladder visualization"**
   - Maturity schedule
   - Income timeline
   - Rollover calendar

4. **"Rate scenario analysis"**
   - +50 bps impact
   - -50 bps impact
   - Portfolio response

---

## 🚨 Important Notes

- Uses simulated yield curves
- Real implementation needs:
  - Bond market data feeds
  - Settlement systems
  - Custodian integration
  - Regulatory compliance
- The analytical framework is production-ready

---

*"Your bonds don't just sit in a portfolio - they're actively managed for yield optimization, credit quality, and duration targeting 24/7."* 