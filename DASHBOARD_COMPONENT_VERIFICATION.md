# 🔍 DASHBOARD COMPONENT VERIFICATION REPORT
**Date:** March 15, 2026  
**Status:** ⚠️ Multiple Issues Found

---

## EXECUTIVE SUMMARY

### 🔴 Critical Issues (Must Fix)
1. **Stock Portfolio P&L Wrong** - Shows ₹0.00, should show ₹-9,083.70
2. **Market Data Missing** - Dashboard Market Overview will be empty
3. **Options P&L Mismatch** - Portfolio shows ₹9,298.50 profit, but position shows ₹-10,455.00 loss

### 🟡 Data Verification Status

| Component | Source Table | Status | Issue |
|-----------|-------------|---------|-------|
| **STOCK TRADING** ||||
| Portfolio Summary | paper_portfolio | ⚠️ WRONG | Shows ₹0.00 P&L, should be ₹-9,083.70 |
| Positions (16) | paper_positions | ✅ OK | Correct data |
| Orders (27) | paper_orders | ✅ OK | Correct data |
| Signals (30) | signals | ✅ OK | Correct data |
| **OPTIONS TRADING** ||||
| Portfolio Summary | paper_options_portfolio | ⚠️ MISMATCH | ₹9,298.50 vs position ₹-10,455.00|
| Positions (1) | paper_options_positions | ✅ OK | Has 1 NIFTY 23500 CE position |
| Orders (5) | paper_options_orders | ✅ OK | Correct data |
| Signals (4) | options_signals | ✅ OK | Correct data |
| **MARKET DATA** ||||
| Market Overview | market_ohlc | ❌ EMPTY | No data - dashboard will be broken |
| Global Indices | global_indices | ✅ OK | 5 indices available |

---

## DETAILED COMPONENT ANALYSIS

### 📊 PART 1: STOCK PAPER TRADING DASHBOARD

#### Component 1: Portfolio Summary Card
**API Endpoint:** `/api/paper-trading/portfolio`  
**Data Source:** `paper_portfolio` table via `VirtualPortfolio.get_portfolio_summary()`

**Current Database Values:**
```
Total Capital:    ₹1,000,000.00
Available Cash:   ₹1,000,000.00  ← WRONG (should be ₹292,087.80)
Invested Amount:  ₹0.00          ← WRONG (should be ₹701,370.00)
Total P&L:        ₹0.00          ← WRONG (should be ₹-9,083.70)
Today P&L:        ₹0.00          ← WRONG (should be ₹-9,083.70)
```

**Actual Values (from paper_positions):**
```
Total Positions:  16
Total P&L:        ₹-9,083.70     ← CORRECT VALUE
Total Invested:   ₹701,370.00    ← CORRECT VALUE
```

**Issue:** The `paper_portfolio` table is NOT being updated when positions change!

**Fix Required:**
1. Update `services/paper_trading/virtual_portfolio.py` to recalculate and update `paper_portfolio` table
2. Or modify API to calculate P&L from positions in real-time (already fixed in `/api/portfolio/summary`)

---

#### Component 2: Open Positions Table
**API Endpoint:** `/api/paper-trading/positions`  
**Data Source:** `paper_positions` table

**Status:** ✅ **WORKING CORRECTLY**

**Sample Data (Top 5 by P&L):**
```
Symbol       Qty   Avg Price  Curr Price  P&L        P&L %
---------------------------------------------------------
HDFCBANK       5    814.50     816.85     +₹11.75    +0.29%
BHARTIARTL     9   1803.20    1804.50     +₹11.70    +0.07%
ICICIBANK      4   1249.90    1252.70     +₹11.20    +0.22%
...
RELIANCE     161   1401.41    1379.50    -₹3,528.30  -1.56%  (Biggest Loss)
INFY         190   1269.72    1249.70    -₹3,804.40  -1.58%  (Biggest Loss)
```

**Dashboard Should Show:**
- 16 total positions
- 3 profitable (HDFCBANK, BHARTIARTL, ICICIBANK with small gains)
- 13 losing positions (rest with losses)
- Total unrealized loss: ₹-9,083.70

---

#### Component 3: Recent Orders Table
**API Endpoint:** `/api/paper-trading/orders?limit=10`  
**Data Source:** `paper_orders` table

**Status:** ✅ **WORKING CORRECTLY**

**Latest Orders:**
```
Order ID                         Symbol      Type   Qty    Price    Status
---------------------------------------------------------------------------
PAPER_EXIT_HCLTECH_1773389515    HCLTECH     SELL   75    1326.30   EXECUTED
PAPER_EXIT_TCS_1773388362        TCS         SELL   69    2402.90   EXECUTED
PAPER_EXIT_WIPRO_1773388362      WIPRO       SELL   110   196.87    EXECUTED
PAPER_EXIT_LT_1773388362         LT          SELL   1     3478.90   EXECUTED
PAPER_SBIN_1773379142            SBIN        BUY    1     1062.80   EXECUTED
...
```

**Dashboard Should Show:**
- 27 total orders (10 most recent)
- Mix of BUY and SELL orders
- All with EXECUTED status

---

#### Component 4: Trading Signals List
**API Endpoint:** `/api/signals/latest?limit=10`  
**Data Source:** `signals` table

**Status:** ✅ **WORKING CORRECTLY**

**Latest Signals:**
```
ID   Symbol        Type   Strategy             Entry     Confidence  Status
--------------------------------------------------------------------------
55   ULTRACEMCO    BUY    MOMENTUM_BREAKOUT   10750.00   70          ACTIVE
54   BAJFINANCE    BUY    MOMENTUM_BREAKOUT   866.20     78          ACTIVE
53   TITAN         BUY    MOMENTUM_BREAKOUT   4112.80    77          ACTIVE
...
```

**Dashboard Should Show:**
- 30 total signals (showing 10 most recent)
- All BUY signals from MOMENTUM_BREAKOUT strategy
- Mix of ACTIVE and PENDING status

---

### 📈 PART 2: NIFTY OPTIONS TRADING DASHBOARD

#### Component 5: Options Portfolio Summary
**API Endpoint:** `/api/options-trading/portfolio`  
**Data Source:** `paper_options_portfolio` table

**Current Database Values:**
```
Total Capital:          ₹1,000,000.00
Available Cash:         ₹981,893.50
Invested Amount:        ₹27,405.00
Total P&L:              ₹9,298.50      ← WRONG!
Today P&L:              ₹9,298.50
Total Premium Paid:     ₹0.00
Total Premium Received: ₹0.00
```

**Actual Position P&L:**
```
NIFTY 23500 CE (3 lots):
  Entry Premium:  ₹182.70 × 3 × 50 = ₹27,405.00
  Current Premium: ₹113.00 × 3 × 50 = ₹16,950.00
  Actual P&L:      ₹16,950 - ₹27,405 = -₹10,455.00  ← CORRECT VALUE
```

**Issue:** Options portfolio shows ₹9,298.50 profit but actual position shows ₹10,455.00 LOSS!

**Fix Required:**
1. Recalculate options portfolio P&L from positions
2. Update `paper_options_portfolio.total_pnl` to reflect actual position P&L

---

#### Component 6: Options Open Positions
**API Endpoint:** `/api/options-trading/positions`  
**Data Source:** `paper_options_positions` table

**Status:** ⚠️ **DATA CORRECT BUT P&L CALCULATION WRONG**

**Current Position:**
```
Symbol: NIFTY
Strike: 23500
Type:   CE (Call)
Expiry: 2026-03-17 (2 days away)
Qty:    3 lots (3 × 50 = 150 contracts)

Entry Premium:   ₹182.70
Current Premium: ₹113.00 (down 38.16%)
Invested:        ₹27,405.00
Current Value:   ₹16,950.00
P&L:             -₹10,455.00    ← Losing position!
P&L %:           -38.16%        ← Significant loss
```

**Dashboard Should Show:**
- 1 open Call option position
- Strike: 23500 CE
- Expiry: Monday (March 17, 2026)
- **Clear LOSS of ₹10,455** (not profit!)

---

#### Component 7: Options Orders
**API Endpoint:** `/api/options-trading/orders?limit=10`  
**Data Source:** `paper_options_orders` table

**Status:** ✅ **WORKING CORRECTLY**

**Order History:**
```
Order ID                    Symbol  Strike  Type  Order  Qty  Premium  Status
-----------------------------------------------------------------------------
OPT20260313133221461828     NIFTY   23500   CE    BUY    1    182.70   EXECUTED
OPT20260313110807858459     NIFTY   23500   CE    BUY    1    182.70   EXECUTED
OPT20260313110807825607     NIFTY   23500   CE    BUY    1    182.70   EXECUTED
OPT20260313110047           NIFTY   23550   PE    SELL   1    322.55   EXECUTED
OPT20260312140720           NIFTY   23550   PE    BUY    1    136.58   EXECUTED
```

**Dashboard Should Show:**
- 5 total options orders
- 3 BUY orders for 23500 CE @ ₹182.70
- Closed positions: 1 PE SELL for profit (₹322.55 - ₹136.58 = ₹185.97 gain)

---

#### Component 8: Options Signals
**API Endpoint:** `/api/options-trading/signals?limit=10` (needs to be created)  
**Data Source:** `options_signals` table

**Status:** ✅ **DATA EXISTS**

**Latest Signals:**
```
ID  Symbol  Strike  Type  Signal  Premium  Confidence  Status
----------------------------------------------------------------
5   NIFTY   23500   CE    BUY     182.70   80          EXECUTED
4   NIFTY   23500   CE    BUY     182.70   80          EXECUTED
2   NIFTY   23500   CE    BUY     182.70   80          EXECUTED
1   NIFTY   23550   PE    BUY     136.58   85          EXECUTED
```

**Dashboard Should Show:**
- 4 options signals
- All EXECUTED (already traded)
- All high confidence (80-85)

---

### 🌍 PART 3: MARKET OVERVIEW DASHBOARD

#### Component 9: Market Data Cards (NIFTY, Bank Nifty, etc.)
**API Endpoint:** `/api/market/overview`  
**Data Source:** `market_ohlc` table

**Status:** ❌ **CRITICAL - NO DATA**

**Current Database:**
```
market_ohlc table: EMPTY (0 rows)
```

**Issue:** Dashboard cannot show:
- NIFTY 50 current price
- Bank Nifty price
- Any stock prices
- Price changes
- Market trend indicators

**Fix Required:**
1. Run `python fetch_all_data.py` to populate market data
2. Set up scheduled job to update market data regularly
3. Or use live API integration

---

#### Component 10: Global Indices
**API Endpoint:** `/api/market/global-indices`  
**Data Source:** `global_indices` table

**Status:** ✅ **WORKING CORRECTLY**

**Available Indices:**
```
Index Name    Value      Change %   Last Updated
------------------------------------------------
^DJI          47,337.20  -0.77%     2026-03-11 23:30
^GSPC          6,761.92  -0.29%     2026-03-11 23:30
^IXIC         22,665.41  -0.14%     2026-03-11 23:30
^FTSE         10,353.77  -0.56%     2026-03-11 23:03
^N225         55,025.37  +1.43%     2026-03-11 23:03
```

**Dashboard Should Show:**
- Dow Jones, S&P 500, Nasdaq, FTSE, Nikkei
- All with slight declines except Nikkei
- Data from March 11 (3 days old - should update)

---

## 🔧 REQUIRED FIXES

### Priority 1: Stock Portfolio P&L (Critical)

**File:** `services/paper_trading/virtual_portfolio.py`

**Issue:** `paper_portfolio` table not updating when positions change

**Solution OPTIONS:**

**Option A: Update Portfolio Table (Recommended)**
Add method to recalculate portfolio from positions:

```python
def update_portfolio_pnl(self):
    """Update portfolio P&L from positions"""
    cursor = self.conn.cursor()
    
    # Calculate from positions
    cursor.execute("""
        SELECT 
            COALESCE(SUM(pnl), 0) as total_pnl,
            COALESCE(SUM(invested_value), 0) as invested,
            COALESCE(SUM(current_value), 0) as current_val
        FROM paper_positions
    """)
    
    result = cursor.fetchone()
    total_pnl, invested, current_val = result
    
    # Update portfolio
    cursor.execute("""
        UPDATE paper_portfolio
        SET total_pnl = %s,
            invested_amount = %s,
            available_cash = total_capital - %s,
            today_pnl = %s,
            updated_at = NOW()
    """, (total_pnl, invested, invested, total_pnl))
    
    self.conn.commit()
    cursor.close()
```

Call this method after every price update.

**Option B: API Real-Time Calculation (Already Done!)**
The `/api/portfolio/summary` endpoint already fixed to calculate from positions.
Just use this endpoint instead of `/api/paper-trading/portfolio`.

---

### Priority 2: Options Portfolio P&L (Critical)

**File:** `services/paper_trading/options_virtual_portfolio.py`

**Issue:** Options portfolio shows wrong P&L (₹9,298.50 profit vs ₹-10,455.00 actual loss)

**Solution:**
Similar to stock portfolio, add method to recalculate from positions:

```python
def update_options_portfolio_pnl(self):
    """Update options portfolio P&L from positions"""
    cursor = self.conn.cursor()
    
    cursor.execute("""
        SELECT 
            COALESCE(SUM(pnl), 0) as total_pnl,
            COALESCE(SUM(invested_value), 0) as invested
        FROM paper_options_positions
    """)
    
    result = cursor.fetchone()
    total_pnl, invested = result
    
    cursor.execute("""
        UPDATE paper_options_portfolio
        SET total_pnl = %s,
            invested_amount = %s,
            today_pnl = %s,
            updated_at = NOW()
    """, (total_pnl, invested, total_pnl))
    
    self.conn.commit()
    cursor.close()
```

---

### Priority 3: Market Data (Critical)

**Issue:** `market_ohlc` table is empty

**Solution:**
```powershell
# Run data fetching script
python fetch_all_data.py

# Or set up automated updates
# Add to scheduler or cron job to run every 5 minutes during market hours
```

---

## 📋 VERIFICATION CHECKLIST

After applying fixes, verify each component:

### Stock Trading Dashboard
- [ ] Portfolio P&L shows **₹-9,083.70** (not ₹0.00)
- [ ] Available Cash shows **₹292,087.80** (not ₹1,000,000)
- [ ] Invested Amount shows **₹701,370.00** (not ₹0)
- [ ] Positions table shows **16 positions**
- [ ] Top losers: INFY (-₹3,804), RELIANCE (-₹3,528)
- [ ] Top gainers: HDFCBANK (+₹11.75), BHARTIARTL (+₹11.70)
- [ ] Orders table shows **27 orders** (10 most recent)
- [ ] Signals shows **30 signals** (10 most recent)

### Options Trading Dashboard
- [ ] Portfolio P&L shows **₹-10,455.00** (not ₹9,298.50)
- [ ] Portfolio shows **LOSS, not profit**
- [ ] Position shows: NIFTY 23500 CE, 3 lots
- [ ] Entry premium: ₹182.70, Current: ₹113.00
- [ ] Position P&L: -38.16%
- [ ] Orders table shows **5 orders**
- [ ] Signals shows **4 signals**

### Market Overview
- [ ] NIFTY 50 price shows (not empty)
- [ ] Bank Nifty shows (not empty)
- [ ] Individual stock prices show
- [ ] Global indices show (Dow, S&P, Nasdaq, etc.)
- [ ] All with proper formatting and colors

---

## 🎯 ACTION PLAN

### Immediate (Now):
1. ✅ Portfolio API already fixed - just restart API server
2. Run `python update_paper_prices.py` to update current prices
3. Run `python fetch_all_data.py` to populate market data

### Short Term (Today):
1. Add portfolio recalculation methods to virtual portfolio classes
2. Fix options P&L calculation
3. Test all dashboard components
4. Update prices regularly (every 5 minutes)

### Long Term (This Week):
1. Set up automated price updates
2. Add price update scheduler
3. Add data validation checks
4. Monitor for P&L calculation accuracy

---

**Status:** Documentation complete. Apply fixes and retest dashboard.
