# Paper Trading Strategies - Comprehensive Guide

**Version**: 1.0  
**Last Updated**: March 12, 2026  
**System**: Automated Market Analysis & Paper Trading Engine  

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Technical Indicators](#technical-indicators)
3. [Trading Strategies](#trading-strategies)
4. [Risk Management](#risk-management)
5. [Position Sizing](#position-sizing)
6. [Entry & Exit Rules](#entry--exit-rules)
7. [Nifty 50 Application](#nifty-50-application)
8. [Signal Confidence System](#signal-confidence-system)
9. [Auto-Execution Engine](#auto-execution-engine)
10. [Performance Monitoring](#performance-monitoring)
11. [Best Practices](#best-practices)

---

## 📊 Overview

### System Architecture

The paper trading system uses **live market data from Zerodha** to execute virtual trades without risking real capital. It combines multiple technical analysis strategies with automated execution based on confidence-scored signals.

**Core Components**:
- **Indicator Engine**: Calculates 15+ technical indicators
- **Strategy Engine**: Generates buy/sell signals from 2+ strategies
- **Paper Trading Engine**: Auto-executes signals with virtual money
- **Virtual Portfolio**: Tracks positions, P&L, and performance
- **Risk Manager**: Controls position sizing and exit conditions

**Capital**: ₹10,00,000 (10 Lakhs) virtual money  
**Market**: NSE (National Stock Exchange India)  
**Focus**: Nifty 50 stocks and liquid mid-caps  
**Timeframes**: 5-minute, 15-minute, 1-hour, Daily  

---

## 🔧 Technical Indicators

The system calculates the following indicators on all OHLC (Open-High-Low-Close) data:

### 1. **Trend Indicators**

#### Exponential Moving Average (EMA)
- **EMA 9**: Fast-moving average (short-term trend)
- **EMA 21**: Medium-term trend
- **EMA 50**: Long-term trend
- **EMA 200**: Long-term trend confirmation

**Usage**: 
- **Bullish**: EMA 9 > EMA 21 > EMA 50
- **Bearish**: EMA 9 < EMA 21 < EMA 50
- **Crossover**: EMA 9 crossing above/below EMA 21 signals trend change

#### MACD (Moving Average Convergence Divergence)
- **MACD Line**: 12-period EMA - 26-period EMA
- **Signal Line**: 9-period EMA of MACD
- **Histogram**: MACD - Signal

**Usage**:
- **Buy**: MACD crosses above Signal Line
- **Sell**: MACD crosses below Signal Line
- **Confirmation**: Histogram increasing = strengthening trend

#### Volume Weighted Average Price (VWAP)
- Calculates average price weighted by volume
- Acts as dynamic support/resistance

**Usage**:
- **Buy**: Price bounces off VWAP from below
- **Sell**: Price rejects at VWAP from above
- **Intraday**: Reset daily at 9:15 AM

### 2. **Momentum Indicators**

#### RSI (Relative Strength Index)
- **Period**: 14
- **Range**: 0-100

**Levels**:
- **Oversold**: < 30 (potential buy)
- **Neutral**: 30-70 (consolidation)
- **Overbought**: > 70 (potential sell)

**Usage**:
- **Buy**: RSI < 40 + bullish divergence
- **Sell**: RSI > 60 + bearish divergence
- **Exit**: RSI reaches extreme (< 20 or > 80)

#### Stochastic Oscillator
- **%K Line**: Fast oscillator
- **%D Line**: 3-period SMA of %K

**Usage**:
- **Buy**: %K crosses above %D in oversold zone (< 20)
- **Sell**: %K crosses below %D in overbought zone (> 80)

### 3. **Volatility Indicators**

#### ATR (Average True Range)
- **Period**: 14
- Measures market volatility

**Usage**:
- **Position Sizing**: Lower ATR = larger position
- **Stop Loss**: 1x ATR below entry (conservative)
- **Target**: 1.5-2x ATR above entry

#### Bollinger Bands
- **Middle**: 20-period SMA
- **Upper**: SMA + (2 × Standard Deviation)
- **Lower**: SMA - (2 × Standard Deviation)

**Usage**:
- **Buy**: Price touches lower band + reversal signal
- **Sell**: Price touches upper band + rejection
- **Volatility**: Bands squeezing = breakout incoming

### 4. **Custom Indicators**

#### Supertrend
- Combines ATR with price action
- **Direction**: +1 (uptrend), -1 (downtrend)

**Usage**:
- **Buy**: Supertrend flips to +1
- **Sell**: Supertrend flips to -1
- **Trailing Stop**: Use supertrend line as dynamic stop

---

## 🎯 Trading Strategies

### Strategy 1: VWAP Trap Strategy

**Best For**: Intraday trading, liquid stocks  
**Timeframe**: 15-minute candles  
**Win Rate**: 65-70%  

#### BUY Signal Conditions

1. **Price Setup**:
   - Price dips **below VWAP**
   - Price bounces back **above VWAP** with volume

2. **RSI Confirmation**:
   - RSI < 40 (oversold territory)
   - RSI rising (momentum building)

3. **Trend Confirmation**:
   - EMA 9 > EMA 21 (uptrend intact)
   - OR recent bullish crossover

4. **Volume**:
   - Current volume > 1.2x average volume (20-period)

5. **MACD Confirmation** (bonus):
   - MACD > Signal Line
   - Histogram positive and increasing

**Entry**: When all conditions met at candle close  
**Stop Loss**: VWAP or 1× ATR below entry (whichever is closer)  
**Target**: 1.5× ATR above entry (or +2-3%)  

#### SELL Signal Conditions

1. **Price Setup**:
   - Price rises **above VWAP**
   - Price falls back **below VWAP** with volume

2. **RSI Confirmation**:
   - RSI > 60 (overbought territory)
   - RSI falling

3. **Trend Confirmation**:
   - EMA 9 < EMA 21 (downtrend)
   - OR recent bearish crossover

4. **Volume**:
   - Current volume > 1.2x average volume

5. **MACD Confirmation** (bonus):
   - MACD < Signal Line
   - Histogram negative and decreasing

**Entry**: When all conditions met at candle close  
**Stop Loss**: VWAP or 1× ATR above entry  
**Target**: 1.5× ATR below entry (or -2-3%)  

#### Confidence Scoring

Base score: **50%**

**Add points for**:
- Volume > 1.2x average: **+15%**
- Strong trend (EMA 9 > 21 > 50): **+20%**
- RSI extreme (< 30 or > 70): **+10%**
- MACD confirmation: **+5%**

**Maximum**: 100%  
**Minimum to execute**: 70%

#### Example Trade

```
Symbol: RELIANCE
Date: March 12, 2026, 10:30 AM

Setup:
- VWAP: ₹1,400
- Price dipped to ₹1,395, bounced to ₹1,402
- RSI: 38 (oversold)
- EMA 9: ₹1,405, EMA 21: ₹1,398
- Volume: 1.4x average
- MACD > Signal

Action: BUY at ₹1,402
SL: ₹1,390 (VWAP - ATR)
Target: ₹1,420 (1.5x ATR)
Confidence: 85%
Result: Exited at ₹1,418 (+₹16/share, +1.14%)
```

---

### Strategy 2: Opening Range Breakout (ORB)

**Best For**: Gap openings, news-driven moves  
**Timeframe**: 5-minute candles  
**Win Rate**: 60-65%  

#### Setup Phase (9:15 AM - 9:30 AM)

1. **Mark Opening Range**:
   - **OR High**: Highest price in first 15 minutes
   - **OR Low**: Lowest price in first 15 minutes
   - **Range**: OR High - OR Low

2. **Wait for Breakout** (9:30 AM onwards)

#### BUY Signal (Upside Breakout)

1. **Price Action**:
   - Price closes **above OR High** by 0.2%
   - Strong bullish candle

2. **Volume Confirmation**:
   - Breakout candle volume > 1.5x average opening range volume

3. **Trend Alignment**:
   - EMA 9 pointing upward
   - No major resistance nearby

**Entry**: Breakout candle close  
**Stop Loss**: OR Low  
**Target**: Entry + (1.5 × Range Height)  

#### SELL Signal (Downside Breakdown)

1. **Price Action**:
   - Price closes **below OR Low** by 0.2%
   - Strong bearish candle

2. **Volume Confirmation**:
   - Breakdown candle volume > 1.5x average

3. **Trend Alignment**:
   - EMA 9 pointing downward
   - No major support nearby

**Entry**: Breakdown candle close  
**Stop Loss**: OR High  
**Target**: Entry - (1.5 × Range Height)  

#### Confidence Scoring

Base score: **55%**

**Add points for**:
- Wide opening range (> 1% of price): **+10%**
- High volume breakout (> 2x avg): **+20%**
- Trend alignment (EMA 9 > 21): **+10%**
- No nearby resistance: **+5%**

**Maximum**: 100%  
**Minimum to execute**: 70%

#### Example Trade

```
Symbol: TCS
Date: March 12, 2026

Opening Range (9:15-9:30):
- OR High: ₹2,470
- OR Low: ₹2,455
- Range: ₹15

Breakout (9:40 AM):
- Price: ₹2,475 (0.2% above OR High)
- Volume: 2.1x average
- EMA 9 trending up

Action: BUY at ₹2,475
SL: ₹2,455 (OR Low)
Target: ₹2,497.50 (Entry + 1.5×Range)
Confidence: 78%
Result: Exited at ₹2,495 (+₹20/share, +0.81%)
```

---

### Strategy 3: RSI Mean Reversion

**Best For**: Range-bound markets, sideways consolidation  
**Timeframe**: Daily or 1-hour  
**Win Rate**: 55-60%  

#### BUY Signal

1. **RSI Oversold**: RSI < 30
2. **Bullish Divergence**: Price making lower lows, RSI making higher lows
3. **Support Level**: Price near major support (EMA 50 or key level)
4. **Volume Spike**: Recent selling exhaustion

**Entry**: When RSI crosses back above 30  
**Stop Loss**: Recent swing low or 2% below entry  
**Target**: RSI 50-60 or +3% profit  

#### SELL Signal

1. **RSI Overbought**: RSI > 70
2. **Bearish Divergence**: Price making higher highs, RSI making lower highs
3. **Resistance Level**: Price near major resistance
4. **Volume Drop**: Buying exhaustion

**Entry**: When RSI crosses back below 70  
**Stop Loss**: Recent swing high or 2% above entry  
**Target**: RSI 40-50 or -3% profit  

---

## 🛡️ Risk Management

### Core Principles

1. **Maximum Risk Per Trade**: 1-2% of capital
   - Capital: ₹10,00,000
   - Max loss per trade: ₹10,000-₹20,000

2. **Maximum Portfolio Risk**: 5% of total capital
   - Never risk more than ₹50,000 across all open positions

3. **Maximum Drawdown**: 10%
   - Stop all trading if portfolio drops below ₹9,00,000
   - Review strategies and resume cautiously

4. **Correlation Risk**: 
   - Don't hold more than 2 positions in same sector
   - Avoid correlated stocks (e.g., HDFCBANK + ICICIBANK)

5. **Position Count**:
   - Maximum 5 open positions simultaneously
   - Ensures focused monitoring

### Stop Loss Rules

**Fixed Stops**:
- **Tight**: -2% (for high-confidence trades)
- **Standard**: -3% (normal trades)
- **Wide**: -5% (swing trades, lower timeframes)

**Dynamic Stops**:
- **ATR-based**: Entry - (1× ATR)
- **VWAP**: Use VWAP as trailing stop
- **Supertrend**: Follow supertrend line

**Trailing Stops**:
- When trade up 2%, move SL to breakeven
- When trade up 4%, trail SL to +2%
- Lock in 50% of gain on way to target

### Profit Targets

**Standard**:
- **Target 1**: +3% (take 50% profit)
- **Target 2**: +5% (take remaining 50%)

**Risk-Reward Ratio**:
- Minimum: 1:1.5 (risk ₹10 to make ₹15)
- Ideal: 1:2 (risk ₹10 to make ₹20)
- Aggressive: 1:3+ (for high-confidence setups)

### Capital Allocation

**Per Trade** (based on confidence):
- **70-75% confidence**: 10% of capital (₹1,00,000)
- **76-85% confidence**: 15% of capital (₹1,50,000)
- **86-95% confidence**: 20% of capital (₹2,00,000)

**Example**:
```
Signal: INFY BUY @ ₹1,270
Confidence: 82%
Capital allocation: 15% = ₹1,50,000
Quantity: ₹1,50,000 / ₹1,270 = 118 shares
Stop Loss: ₹1,245 (-₹25)
Risk per share: ₹25
Total risk: 118 × ₹25 = ₹2,950 (0.3% of capital ✓)
```

---

## 📏 Position Sizing

### Formula-Based Sizing

**Kelly Criterion** (Conservative):
```
Position Size % = (Win Rate × Avg Win) - (Loss Rate × Avg Loss) / Avg Win
                 × Kelly Multiplier (0.25 for conservative)
```

**Fixed Fractional**:
```
Shares = (Capital × Risk %) / (Entry Price - Stop Loss Price)
```

**Volatility-Adjusted**:
```
Position Size = Base Size × (Average ATR / Current ATR)
```

### Practical Example

```python
# Given
capital = 1000000  # ₹10 Lakhs
risk_percent = 1.0  # 1% risk
entry_price = 1500
stop_loss = 1470  # 2% below entry

# Calculate
risk_per_share = entry_price - stop_loss  # ₹30
total_risk = capital * (risk_percent / 100)  # ₹10,000
shares = total_risk / risk_per_share  # 333 shares

# Position value
position_value = shares × entry_price  # ₹4,99,500 (49.95% of capital)

# Validate: If SL hit, loss = 333 × ₹30 = ₹9,990 ≈ 1% ✓
```

---

## 🚪 Entry & Exit Rules

### Entry Checklist

Before entering **ANY** trade, verify:

- [ ] **Signal valid**: All strategy conditions met
- [ ] **Confidence ≥ 70%**: Minimum threshold
- [ ] **Risk acceptable**: Loss won't exceed 2% if SL hit
- [ ] **Position size correct**: Calculated per formula
- [ ] **Market hours**: 9:15 AM - 3:15 PM (avoid last 15 min)
- [ ] **No correlation**: Not duplicate position
- [ ] **Capital available**: Sufficient cash for trade
- [ ] **Stop loss defined**: Clear exit if wrong
- [ ] **Target defined**: Clear profit objective
- [ ] **Volume adequate**: Can exit without slippage

### Exit Conditions

**Exit immediately if**:

1. **Stop Loss Hit**: -2% or predefined SL level
2. **Target Achieved**: +3% or predefined target
3. **End of Day**: Close all positions at 3:15 PM (for intraday)
4. **Signal Reversal**: Opposite signal generated
5. **Market Close**: Approaching 3:30 PM

**Partial Exit Scenarios**:

1. **Hit 50% of target**: Exit 50% of position, trail SL
2. **Strong momentum**: Hold for full target
3. **Weakening momentum**: Exit early at +2%

**Hold Scenarios**:

- Price consolidating near entry (within ±0.5%)
- Indicators still aligned with original signal
- No major news/events disrupting thesis
- Time left till target (max 2-3 days for swing)

---

## 📈 Nifty 50 Application

### Best Nifty 50 Stocks for Paper Trading

#### High Success Rate (Liquid & Trending)
1. **RELIANCE** - Strong trends, respects technical levels
2. **TCS** - Consistent mover, good for ORB
3. **INFY** - High liquidity, VWAP trap works well
4. **HDFCBANK** - Banking sector leader
5. **ICICIBANK** - Good intraday volatility

#### Moderate Success (More Choppy)
6. **WIPRO** - Range-bound often
7. **AXISBANK** - Volatile, wider stops needed
8. **LT** - Engineering sector plays
9. **MARUTI** - Auto sector leader
10. **SUNPHARMA** - Pharma sector proxy

#### Avoid (Too Slow/Choppy)
- **NESTLEIND** - Very slow mover
- **HINDUNILVR** - FMCG, low volatility
- **TITAN** - Wide bid-ask spread

### Sector Rotation Strategy

**Week 1-2**: Focus on IT (TCS, INFY, WIPRO)  
**Week 3-4**: Focus on Banking (HDFC, ICICI, AXIS)  
**Month-end**: Focus on Index heavyweights (RELIANCE)

### Nifty 50 Index Trading

Can also trade **Nifty 50 Index** futures/options:

**Strategy**: Opening Range Breakout  
**Timeframe**: 5-minute  
**Stop Loss**: Tighter (0.5% for index)  
**Target**: 1-1.5% (index moves slower)  

---

## 🎯 Signal Confidence System

### Confidence Calculation

Each strategy calculates confidence (0-100%) based on:

#### Base Score: 50%

#### Bonus Points:
- **Volume Confirmation**: +10-15%
- **Trend Alignment**: +15-20%
- **Multiple Indicator Confluence**: +10%
- **RSI Extreme**: +5-10%
- **MACD Confirmation**: +5%
- **Price at Key Level**: +10%

### Confidence Tiers

| Confidence | Action | Risk | Position Size |
|------------|--------|------|---------------|
| **90-100%** | Strong BUY/SELL | High conviction | 20% capital |
| **80-89%** | BUY/SELL | Good setup | 15% capital |
| **70-79%** | Consider | Acceptable | 10% capital |
| **60-69%** | Monitor | Too risky | Skip |
| **< 60%** | Ignore | Invalid signal | No trade |

### Signal Filtering

**Minimum confidence to execute**: 70%

Paper trading engine will:
- Fetch all signals from database
- Filter signals with confidence ≥ 70%
- Sort by confidence (highest first)
- Execute top signals until capital deployed

---

## ⚙️ Auto-Execution Engine

### How It Works

```
1. Every 60 seconds:
   ├─ Fetch live prices from Zerodha
   ├─ Update all open positions with current P&L
   ├─ Check exit conditions (target/SL)
   └─ Check pending signals

2. For each pending signal:
   ├─ Check if price matches entry (±2% tolerance)
   ├─ Verify confidence ≥ 70%
   ├─ Calculate position size
   ├─ Verify capital available
   └─ Execute virtual order

3. For each open position:
   ├─ Calculate current P&L %
   ├─ If P&L ≥ +3%: Exit with profit
   ├─ If P&L ≤ -2%: Exit with stop loss
   └─ Update unrealized P&L
```

### Execution Logic

**Entry Trigger**:
```python
if signal.confidence >= 70:
    current_price = get_live_price(signal.symbol)
    entry_price = signal.entry_price
    
    # Within 2% of signal price?
    price_diff = abs(current_price - entry_price) / entry_price
    
    if price_diff <= 0.02:  # 2% tolerance
        execute_order(signal, current_price)
```

**Exit Trigger**:
```python
for position in open_positions:
    pnl_percent = position.pnl_percent
    
    if pnl_percent >= 3.0:  # Target hit
        exit_position(position, reason="Target")
    
    elif pnl_percent <= -2.0:  # Stop loss hit
        exit_position(position, reason="Stop Loss")
```

### Market Hours Check

Engine only operates during:
- **Monday-Friday**: 9:15 AM - 3:30 PM IST
- **Weekends**: Paused
- **Holidays**: Paused (NSE calendar)

---

## 📊 Performance Monitoring

### Key Metrics

#### Win Rate
```
Win Rate = (Winning Trades / Total Trades) × 100
Target: > 60%
```

#### Average Win/Loss
```
Avg Win = Total Profit from Wins / Number of Wins
Avg Loss = Total Loss from Losses / Number of Losses
```

#### Profit Factor
```
Profit Factor = Gross Profit / Gross Loss
Target: > 1.5
```

#### Sharpe Ratio
```
Sharpe = (Avg Return - Risk-Free Rate) / Std Dev of Returns
Target: > 1.0
```

#### Maximum Drawdown
```
Max DD = (Peak Value - Trough Value) / Peak Value
Target: < 15%
```

### Daily Review Checklist

**Morning (9:00 AM)**:
- [ ] Check pending signals
- [ ] Review overnight news
- [ ] Check global markets
- [ ] Verify Zerodha token active
- [ ] Confirm API/Dashboard running

**Intraday (Every 2 hours)**:
- [ ] Monitor open positions
- [ ] Check P&L status
- [ ] Watch for exit triggers
- [ ] Review new signals

**Evening (4:00 PM)**:
- [ ] Calculate day's P&L
- [ ] Review closed trades
- [ ] Analyze wins/losses
- [ ] Update trading journal
- [ ] Plan for tomorrow

### Performance Dashboard

Access at: `http://localhost:3000/paper-trading`

**Key Sections**:
1. **Portfolio Summary**: Capital, cash, invested, P&L
2. **Trading Stats**: Orders, win rate, profit factor
3. **Current Positions**: Live P&L tracking
4. **Recent Orders**: Execution history
5. **Charts**: P&L curve, equity curve

---

## ✅ Best Practices

### Do's ✓

1. **Follow the System**: Trust the indicators and strategies
2. **Respect Stop Losses**: Exit when SL hit, no exceptions
3. **Size Properly**: Never risk more than 2% per trade
4. **Keep Journal**: Document all trades with reasons
5. **Review Weekly**: Analyze performance, adjust if needed
6. **Wait for Setup**: Patience for high-confidence signals
7. **Diversify**: Multiple stocks, avoid concentration
8. **Use Trailing Stops**: Lock in profits as trade moves
9. **Trade Liquid Stocks**: Nifty 50 primary focus
10. **Monitor News**: Be aware of major events

### Don'ts ✗

1. **Don't Overtrade**: Quality over quantity
2. **Don't Average Down**: Doubling losing positions
3. **Don't Ignore SL**: Hoping trade will reverse
4. **Don't Chase**: Enter only at defined levels
5. **Don't Revenge Trade**: After a loss, stay disciplined
6. **Don't Use All Capital**: Keep 30-40% reserve
7. **Don't Trade Low-Volume**: Stick to liquid stocks
8. **Don't Overthin**: System trades, not gut feel
9. **Don't Trade Last 15 Min**: Avoid 3:15-3:30 PM
10. **Don't Add Without Plan**: Position sizing already calculated

### Common Mistakes to Avoid

| Mistake | Impact | Solution |
|---------|--------|----------|
| **Moving stop loss** | Larger losses | Define SL at entry, honour it |
| **Taking profits early** | Reduced edge | Let winners run to target |
| **Overtrading** | High costs, fatigue | Max 3-5 trades/day |
| **Ignoring trends** | Fighting tape | Trade with trend, not against |
| **Position sizing errors** | Excessive risk | Use formula, verify |
| **No trade journal** | Can't improve | Document every trade |
| **Emotional trading** | Irrational decisions | Stick to system rules |

---

## 📚 Strategy Summary Table

| Strategy | Timeframe | Win Rate | Best For | Risk:Reward | Confidence |
|----------|-----------|----------|----------|-------------|------------|
| **VWAP Trap** | 15-min | 65-70% | Intraday, trending | 1:1.5 | 75-85% |
| **Opening Range Breakout** | 5-min | 60-65% | Gaps, momentum | 1:2 | 70-80% |
| **RSI Mean Reversion** | Daily | 55-60% | Range-bound | 1:2 | 70-75% |
| **EMA Crossover** | 1-hour | 55-60% | Trending | 1:1.5 | 65-75% |

---

## 🎓 Learning Path

### Week 1: Understanding
- Read this document cover-to-cover
- Watch live signals being generated
- Observe trades without interference
- Study indicator meanings

### Week 2: Analysis
- Review all executed trades
- Understand why each trade was taken
- Analyze wins and losses
- Study confidence calculation

### Week 3: Optimization
- Identify best-performing strategies
- Note ideal market conditions
- Optimize position sizing
- Refine entry timing

### Week 4: Independent Trading
- Start monitoring manually
- Verify auto-execution logic
- Keep detailed journal
- Measure personal performance

---

## 🛠️ Tools & Commands

### Morning Routine (NEW! ⭐)
```bash
# Run complete morning analysis (9:00 AM daily)
py morning_routine.py
```

**What it does (AUTOMATED)**:
- ✅ Verifies Zerodha token validity
- ✅ Fetches live options chain (NIFTY + BANKNIFTY)
- ✅ Checks India VIX level
- ✅ Calculates PCR ratio (OI & Volume)
- ✅ Identifies Max Pain strike
- ✅ Analyzes OI buildup (top strikes)
- ✅ Generates fresh trading signals
- ✅ Reviews current positions
- ✅ Provides market analysis & recommendations

**Output**: Complete pre-market checklist in one command!

---

### Check Current Status
```bash
# View all trades with timestamps
py verify_all_timestamps.py

# Check portfolio status
py show_actual_trade_times.py

# List available signals
py check_signals.py

# View database tables
py list_tables.py
```

### Reset & Restart
```bash
# Reset portfolio to ₹10L
py reset_paper_trading.py

# Activate new signals
py activate_signals.py

# Start paper trading engine
py start_paper_trading.py
```

### API Endpoints
```bash
# Portfolio summary
GET http://localhost:8000/api/paper-trading/portfolio

# Current positions
GET http://localhost:8000/api/paper-trading/positions

# Order history
GET http://localhost:8000/api/paper-trading/orders

# Trading statistics
GET http://localhost:8000/api/paper-trading/stats
```

---

## 📞 Support & Resources

### System Files
- **Engine**: `services/paper_trading/paper_trading_engine.py`
- **Portfolio**: `services/paper_trading/virtual_portfolio.py`
- **Strategies**: `services/strategy/strategies/`
- **Indicators**: `services/indicators/indicator_engine.py`

### Documentation
- **API Guide**: `PAPER_TRADING_GUIDE.md`
- **Architecture**: `ARCHITECTURE.md`
- **Scripts**: `SCRIPTS_GUIDE.md`
- **System Status**: `SYSTEM_STATUS.md`

### Monitoring
- **Dashboard**: http://localhost:3000/paper-trading
- **API Docs**: http://localhost:8000/api/docs
- **Logs**: Check terminal output for real-time updates

---

## 🎯 Success Metrics

### Monthly Goals

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| **Win Rate** | > 55% | > 60% | > 65% |
| **Profit Factor** | > 1.3 | > 1.5 | > 2.0 |
| **Monthly Return** | > 3% | > 5% | > 8% |
| **Max Drawdown** | < 15% | < 10% | < 5% |
| **Avg Risk:Reward** | > 1:1.5 | > 1:2 | > 1:3 |
| **Trades Taken** | 20-30 | 30-50 | 50+ |

### Portfolio Milestones

- **Week 1**: ₹10,00,000 → ₹10,20,000 (+2%)
- **Month 1**: ₹10,00,000 → ₹10,50,000 (+5%)
- **Quarter 1**: ₹10,00,000 → ₹11,50,000 (+15%)
- **Year 1**: ₹10,00,000 → ₹15,00,000 (+50%)

---

---

## 🎲 NIFTY 50 OPTIONS TRADING STRATEGIES

### Overview

The system now includes **Nifty 50 Options Trading** for CE (Call) and PE (Put) options paper trading with live market data.

**Capital**: ₹10,00,000 (10 Lakhs) dedicated options capital  
**Contract**: Nifty 50 Index Options (Lot Size: 50)  
**Expiry**: Weekly expiry (nearest Thursday)  
**Target**: +60% to +80% premium gain  
**Stop Loss**: -40% to -50% premium loss  

---

### Options Strategy 1: Opening Range Breakout (Options)

**Best For**: Gap openings, strong directional moves  
**Timeframe**: 5-minute  
**Win Rate**: 60-65%  

#### Setup (9:15 AM - 9:30 AM)
1. Capture Nifty opening range (OR High and OR Low)
2. Wait for breakout after 9:30 AM

#### BUY CE (Call) Signal
1. **Breakout**: Nifty closes above OR High by 0.3%
2. **Strike Selection**: ATM (At-The-Money)
3. **Entry**: Current premium
4. **Target**: Entry premium + 60%
5. **Stop Loss**: Entry premium - 40%

**Example**:
```
OR High: 24,000
Breakout: 24,075 (0.3% above)
Strike: 24,000 CE (ATM)
Entry Premium: ₹120
Target: ₹192 (+60%)
Stop Loss: ₹72 (-40%)
Lot Size: 1 lot (50 contracts)
Investment: ₹6,000
Max Loss: ₹2,400
Max Gain: ₹3,600
```

#### BUY PE (Put) Signal
1. **Breakdown**: Nifty closes below OR Low by 0.3%
2. **Strike Selection**: ATM
3. **Entry**: Current premium
4. **Target**: +60%
5. **Stop Loss**: -40%

**Confidence Scoring**: Base 50 + Breakout (20) + Wide Range (15) + IV (10) + Liquidity (5) = Max 100%

---

### Options Strategy 2: Volatility Spike (IV Spike)

**Best For**: High volatility days (VIX > 15)  
**Timeframe**: Intraday  
**Win Rate**: 55-60%  

#### Entry Rules

**BUY CE** (Bullish):
1. **IV Rank > 60**: High implied volatility
2. **PCR < 0.8**: Low Put-Call Ratio (bullish sentiment)
3. **Strike**: OTM (Out-The-Money) by 100 points
4. **Target**: +80% premium
5. **Stop Loss**: -50% premium

**BUY PE** (Bearish):
1. **IV Rank > 60**: High volatility
2. **PCR > 1.2**: High Put-Call Ratio (bearish sentiment)
3. **Strike**: OTM by 100 points
4. **Target**: +80%
5. **Stop Loss**: -50%

**Example**:
```
Nifty Spot: 24,000
IV Rank: 72% (High)
PCR: 0.65 (Bullish)
Action: BUY 24,100 CE (OTM)
Entry Premium: ₹80
Target: ₹144 (+80%)
Stop Loss: ₹40 (-50%)
Risk: ₹2,000
Reward: ₹3,200
R:R = 1:1.6
```

---

### Options Strategy 3: OI Buildup Momentum

**Best For**: Tracking institutional activity  
**Timeframe**: Intraday  
**Win Rate**: 60-65%  

#### Entry Rules

1. **Detect OI Buildup**: Open Interest increase > 15% at a strike
2. **Direction**: Follow the OI buildup
   - CE buildup = Bullish → BUY CE
   - PE buildup = Bearish → BUY PE
3. **Strike**: The strike with highest OI change
4. **Target**: +70%
5. **Stop Loss**: -45%

**Example**:
```
Strike 24,000 CE: OI increased by 2,50,000 contracts (+18%)
Interpretation: Bullish buildup
Action: BUY 24,000 CE
Entry Premium: ₹100
Target: ₹170 (+70%)
Stop Loss: ₹55 (-45%)
Reason: Institutional CE buying detected
```

---

## 🛡️ Options Risk Management

### Core Principles

1. **Maximum Risk Per Trade**: 2-5% of capital
   - Capital: ₹10,00,000
   - Max loss per trade: ₹20,000-₹50,000

2. **Position Sizing**:
   - High Confidence (80%+): 2-3 lots
   - Medium Confidence (70-79%): 1-2 lots
   - Never more than 5 open option positions

3. **Time Decay Management**:
   - Exit 1 day before expiry
   - Avoid positions with < 2 days to expiry
   - Close all positions at 3:00 PM (intraday strategies)

4. **Volatility Rules**:
   - Don't buy options when IV Rank > 80 (overpriced)
   - Prefer buying when IV Rank 40-70
   - Exit if IV collapses > 20%

### Exit Conditions

**Mandatory Exits**:
1. **Target Hit**: +60% to +80% (based on strategy)
2. **Stop Loss**: -40% to -50%
3. **Time Decay**: 1 day before expiry
4. **End of Day**: 3:00 PM for intraday strategies
5. **IV Collapse**: IV drops > 25% suddenly

### Options-Specific Metrics

**Greeks to Monitor** (future enhancement):
- **Delta**: 0.3-0.7 (ideal range for directional trades)
- **Theta**: Time decay per day
- **Vega**: IV sensitivity

---

## 📊 Options Performance Monitoring

### Key Metrics

#### Win Rate
```
Target: > 55% (options are riskier than stocks)
```

#### Average R:R
```
Target: > 1:1.5 (Risk ₹1 to make ₹1.50)
```

#### Premium Efficiency
```
Avg Premium Paid / Avg Premium Received
Target: > 1.5 (make 50% more than you risk)
```

### Daily Review

**Morning** (9:00 AM) - **AUTOMATED**:

Run the automated morning routine:
```bash
py morning_routine.py
```

This automatically:
- [x] Verifies Zerodha token is valid
- [x] Fetches latest options chain from Zerodha
- [x] Checks India VIX level
- [x] Calculates PCR ratio (OI & Volume)
- [x] Identifies max pain level
- [x] Checks option chain for OI buildup
- [x] Generates fresh trading signals
- [x] Reviews existing positions
- [x] Provides market analysis and recommendations

**Manual Alternative** (if you prefer step-by-step):
- [ ] Check India VIX level: See morning routine output
- [ ] Calculate PCR ratio: `py generate_options_signals.py` (includes PCR)
- [ ] Identify max pain level: Included in signal generation
- [ ] Check option chain for OI buildup: Automatic in strategies
- [ ] Generate fresh signals: `py generate_options_signals.py`

**Evening** (4:00 PM):
- [ ] Run end-of-day report
- [ ] Analyze closed trades
- [ ] Review what went well/wrong
- [ ] Calculate daily P&L
- [ ] Plan for next day

---

## 🎯 Options vs Stocks - Key Differences

| Aspect | Stocks | Options |
|--------|--------|---------|
| **Capital Required** | Higher | Lower (leverage) |
| **Risk** | Price drop | Premium loss (100%) |
| **Time Decay** | None | Theta decay daily |
| **Profit Potential** | Moderate | High (50-100%+) |
| **Stop Loss** | -2% to -3% | -40% to -50% |
| **Target** | +3% to +5% | +60% to +80% |
| **Hold Duration** | Days/weeks | Hours/days |
| **Expiry** | None | Weekly/monthly |

---

## 🛠️ Options Trading Commands

### Initialize Options System
```bash
# First time setup (creates all tables)
py initialize_options_trading.py
```

### Generate Signals
```bash
# Scan for options opportunities
py generate_options_signals.py
```

### Start Options Trading
```bash
# Auto-execute options trades
py start_options_trading.py
```

### End-of-Day Report
```bash
# What went well/wrong analysis
py options_eod_report.py
```

### Check Options Portfolio
```bash
# View positions and P&L
py check_options_portfolio.py
```

---

## 📚 Options Learning Path

### Week 1: Understanding Options
- Study CE vs PE mechanics
- Learn about PCR, IV, max pain
- Observe signal generation
- Don't trade - just learn

### Week 2: Paper Trading
- Start with 1 lot per trade
- Focus on ORB strategy only
- Keep detailed journal
- Review every trade

### Week 3: Advanced Strategies
- Add IV Spike strategy
- Try OI Buildup strategy
- Experiment with strike selection
- Compare performance

### Week 4: Optimization
- Identify best strategy
- Optimize entry timing
- Refine stop loss levels
- Calculate optimal position size

---

## ⚠️ Options Trading Warnings

### Common Mistakes

1. **Overleveraging**: Don't use entire capital on options
2. **Holding Till Expiry**: Theta decay accelerates last day
3. **Ignoring IV**: Don't buy expensive options (IV > 80)
4. **No Stop Loss**: Options can go to zero - use SL
5. **Overtrading**: Max 3-5 option trades per day

### Risk Warnings

- ⚠️ **Options can expire worthless** (total loss)
- ⚠️ **Time decay works against you** (theta)
- ⚠️ **High volatility = High risk**
- ⚠️ **Leverage amplifies both gains AND losses**
- ⚠️ **Weekly expiry = faster decay**

---

## 📈 Options Success Metrics

### Monthly Targets

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| **Win Rate** | > 50% | > 55% | > 60% |
| **Profit Factor** | > 1.5 | > 2.0 | > 2.5 |
| **Monthly Return** | > 10% | > 15% | > 20% |
| **Max Drawdown** | < 20% | < 15% | < 10% |
| **Avg R:R** | > 1:1.5 | > 1:2 | > 1:2.5 |

### Portfolio Milestones (Options)

- **Week 1**: ₹10,00,000 → ₹10,50,000 (+5%)
- **Month 1**: ₹10,00,000 → ₹11,50,000 (+15%)
- **Quarter 1**: ₹10,00,000 → ₹13,00,000 (+30%)
- **Year 1**: ₹10,00,000 → ₹20,00,000 (+100%)

---

## 🔄 Version History

- **v2.0** (March 12, 2026): **OPTIONS TRADING ADDED** 🚀
  - Nifty 50 CE/PE options trading
  - 3 options strategies (ORB, IV Spike, OI Buildup)
  - Options-specific indicators (PCR, IV Rank, Max Pain)
  - Auto-execution engine for options
  - End-of-day analytics with learning insights
  - Options risk management framework

- **v1.0** (March 12, 2026): Initial comprehensive documentation
  - VWAP Trap Strategy
  - Opening Range Breakout Strategy
  - RSI Mean Reversion
  - Auto-execution engine
  - Risk management framework
  - Nifty 50 application guide

---

## 📝 Notes

**Remember**: Paper trading is for *learning and validation*. The goal is to:
1. Understand how strategies work
2. Build confidence in the system
3. Refine risk management
4. Validate before using real money

**Mindset**: Trade with discipline. Every trade is a learning opportunity. Focus on process, not profits.

---

**Happy Paper Trading! 📊🚀**

*For questions or issues, review the system logs or check the dashboard for real-time status.*
