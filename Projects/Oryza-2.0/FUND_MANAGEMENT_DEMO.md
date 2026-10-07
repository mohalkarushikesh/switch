# 🧺 Mutual Funds & ETFs - Autonomous Management Demo

## Overview
The Oryza platform now features **fully autonomous mutual fund and ETF management** with multi-agent analysis, automatic switching, and tax-loss harvesting.

---

## 🚀 Features Implemented

### 1. **Multi-Agent Fund Analysis**
- **Performance Agent**: Analyzes returns, Sharpe ratio, alpha, category comparison
- **Risk Agent**: Evaluates volatility, drawdown, risk-adjusted returns
- **Tax Agent**: Monitors tax implications, identifies harvesting opportunities
- **Category Agent**: Compares within category, expense ratios, fund size

### 2. **Automatic Fund Switching**
- Continuously monitors fund performance
- Switches to better-performing funds when:
  - Current fund underperforms category by >2%
  - Better Sharpe ratio alternatives exist
  - Consensus score drops below 60%

### 3. **Tax-Loss Harvesting**
- Identifies losses > ₹1,000
- Automatically executes tax-saving switches
- Maintains similar exposure while realizing losses
- Tracks LTCG/STCG status

---

## 📊 Available Funds

### Equity Funds
- **HDFC Top 100**: Large cap, 1Y return: 28.5%
- **Axis Bluechip**: Large cap, 1Y return: 25.3%
- **Kotak Emerging**: Mid cap, 1Y return: 35.2%

### Debt Funds
- **ICICI Liquid**: Low risk, 1Y return: 6.8%

### ETFs
- **Nifty BeES**: Index tracking, Expense: 0.05%
- **Gold BeES**: Gold ETF, 1Y return: 12.3%
- **Motilal Nasdaq 100**: International, 1Y return: 32.5%

---

## 🎮 Demo Walkthrough

### Step 1: View Your Fund Portfolio
1. Navigate to Trading → Mutual Funds & ETFs
2. See your current holdings with live NAV updates
3. View allocation chart showing diversification

### Step 2: Enable AI Optimization
1. Click "Enable AI Optimization" button
2. System begins monitoring all funds 24/7
3. Automatic analysis every minute

### Step 3: Watch Multi-Agent Analysis
1. Click any fund to see detailed analysis
2. Four agents provide specialized insights:
   - **Performance**: "Outperforming category by +3.2%"
   - **Risk**: "Volatility: 15.3%, Acceptable"
   - **Tax**: "LTCG Eligible, No harvest opportunity"
   - **Category**: "Rank 5/120, Below avg expense"

### Step 4: Observe Automatic Actions
- **Yellow Alert**: "3 Optimization Opportunities"
- **Tax Harvest**: "Switch HDFC fund to Axis - Save ₹2,500 tax"
- **Performance Switch**: "Kotak outperforming - Switch recommended"

---

## 🤖 How It Works

### Fund Analysis Pipeline
```
Every 60 seconds:
1. Update all fund NAVs
2. Run 4-agent analysis on each fund
3. Build consensus (0-100% confidence)
4. If consensus < 60% → Find better alternatives
5. If tax loss > ₹1,000 → Execute harvest
6. Update user positions automatically
```

### Consensus Algorithm
- **Performance Weight**: 30%
- **Risk Weight**: 25%
- **Tax Weight**: 25%
- **Category Weight**: 20%

### Switch Decision Matrix
| Consensus Score | Action | Description |
|----------------|--------|-------------|
| > 80% | ACCUMULATE | Strong performer - increase allocation |
| 60-80% | HOLD | Continue holding |
| < 60% | SWITCH | Find better alternative |
| Tax Loss | HARVEST | Realize loss, switch to similar fund |

---

## 📈 Expected Behaviors

### Normal Market
- Gradual NAV changes
- Occasional rebalancing suggestions
- Monthly performance reviews

### Market Volatility
- More frequent analysis updates
- Tax harvesting opportunities appear
- Risk agent becomes more active

### Year-End
- Aggressive tax-loss harvesting
- LTCG optimization
- Portfolio rebalancing

---

## 💡 Key Differentiators

1. **True Multi-Agent System**
   - Not just one analysis - 4 specialized agents
   - Each agent has unique expertise
   - Consensus prevents rash decisions

2. **Automatic Execution**
   - No manual intervention needed
   - Switches happen seamlessly
   - Maintains target allocation

3. **Tax Intelligence**
   - Knows purchase dates and tax status
   - Harvests losses optimally
   - Considers indexation benefits

4. **Category Optimization**
   - Always finds top quartile funds
   - Considers expense ratios
   - Tracks fund manager changes

---

## 🎯 Demo Scenarios

### Scenario 1: Tax Harvesting
1. HDFC fund shows -₹3,000 loss
2. Tax agent identifies opportunity
3. Finds Axis Bluechip as replacement
4. Executes switch automatically
5. Saves ₹900 in taxes

### Scenario 2: Performance Switch
1. Current fund returns: 12%
2. Category average: 18%
3. Identifies top performer: 22%
4. Consensus: 85% to switch
5. Moves to better fund

### Scenario 3: Risk Adjustment
1. Market volatility increases
2. Risk agent flags high beta funds
3. Suggests move to liquid funds
4. Rebalances portfolio

---

## 📊 Visual Indicators

### Fund Cards
- 🟢 Green: Outperforming
- 🟡 Yellow: Monitor closely
- 🔴 Red: Consider switching

### Agent Scores
- Performance: Bar chart 0-10
- Risk: Color-coded rating
- Tax: Harvest opportunity flag
- Category: Rank position

### Consensus Display
- Background color changes with score
- Action prominently displayed
- Confidence percentage shown
- Alternative funds listed

---

## 🔔 Notifications

- "Tax harvest executed: Saved ₹1,500"
- "Fund switched: Now in top decile"
- "Risk reduced: Moved to stable fund"
- "Opportunity: 5% extra returns available"

---

## 🛠️ Customization

### Conservative Investors
- Higher threshold for switching (70%)
- Focus on large cap funds
- Prioritize tax efficiency

### Aggressive Investors
- Lower switch threshold (50%)
- Include small/mid cap funds
- Maximize returns over tax

### Balanced Approach
- Default 60% threshold
- Mix of equity and debt
- Optimize both returns and tax

---

## 📈 Performance Tracking

The system tracks:
- Number of switches executed
- Tax saved through harvesting
- Improvement in returns
- Risk-adjusted performance
- Category rank improvements

---

## ⚡ Live Demo Points

1. **"Watch the NAVs update in real-time"**
   - Point to changing values
   - Show day change percentages

2. **"See how agents disagree but reach consensus"**
   - Performance says BUY
   - Risk says CAUTION
   - Consensus: HOLD

3. **"Tax harvesting in action"**
   - Show negative returns
   - Identify harvest opportunity
   - Execute switch live

4. **"Category leader identification"**
   - Current fund: Rank 45/120
   - Better option: Rank 3/120
   - Automatic upgrade

---

## 🚨 Important Notes

- Uses simulated fund data for demo
- Real implementation would need:
  - AMC APIs for real NAVs
  - Demat integration for execution
  - SEBI compliance for advice
  - Tax calculation APIs
- The multi-agent logic is production-ready

---

*"Your funds don't just sit there - they actively seek better opportunities, harvest tax losses, and optimize returns 24/7."* 