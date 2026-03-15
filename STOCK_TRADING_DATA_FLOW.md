# Stock Trading Page - Complete Data Flow Analysis

**Last Updated:** March 14, 2026  
**Component:** Stock Paper Trading System

---

## 🎯 Overview

The stock trading page displays virtual portfolio positions with **live market prices** updated every 30 seconds (frontend) and 60 seconds (backend engine).

### Key Files:
1. **Frontend:** `dashboard/pages/paper-trading.tsx` (React/Next.js)
2. **API Router:** `services/api/routers/paper_trading.py` (FastAPI)
3. **Portfolio Service:** `services/paper_trading/virtual_portfolio.py`
4. **Trading Engine:** `services/paper_trading/paper_trading_engine.py`
5. **Signal Generator:** `generate_nifty50_signals.py`
6. **Market Data:** `services/market_data/adapters/zerodha_adapter.py`

---

## 📊 Complete Data Flow

```
[User Views Dashboard]
         ↓
[Frontend: paper-trading.tsx]
         ↓ (HTTP GET every 30s)
[API: /api/paper-trading/positions]
         ↓
[VirtualPortfolio.get_positions()]
         ↓ (SQL SELECT)
[Database: paper_positions table]
         ↑ (SQL UPDATE every 60s)
[PaperTradingEngine.update_portfolio_prices()]
         ↑ (Fetch live prices)
[ZerodhaAdapter.kite.ltp()]
         ↑
[Zerodha API - Live Market Data]
```

---

## 🔍 Line-by-Line Code Review

### 1️⃣ FRONTEND - Data Fetching & Display

**File:** `dashboard/pages/paper-trading.tsx`

#### **Lines 1-50: Imports and Type Definitions**
```typescript
import { useState, useEffect } from 'react';  // React hooks for state
import Head from 'next/head';                  // Page metadata
import Link from 'next/link';                  // Navigation

interface Portfolio {
  total_capital: number;      // Initial + realized P&L
  available_cash: number;     // Cash available for trading
  invested_amount: number;    // Currently locked in positions
  total_pnl: number;          // Unrealized + realized P&L
  today_pnl: number;          // P&L since market open
  positions_count: number;    // Number of open positions
  updated_at: string;         // Last update timestamp
}

interface Position {
  id: number;
  symbol: string;             // Stock symbol (e.g., "INFY")
  quantity: number;           // Number of shares held
  avg_price: number;          // Average buying price
  current_price: number | null;  // Live market price (can be null)
  invested_value: number;     // quantity * avg_price
  current_value: number | null;  // quantity * current_price
  pnl: number | null;         // current_value - invested_value
  pnl_percent: number | null; // (pnl / invested_value) * 100
  position_type: string;      // "LONG" or "SHORT"
  opened_at: string;          // Position open timestamp
}
```

**💡 Key Design Decision:** 
- `current_price`, `current_value`, `pnl` are **nullable** (`| null`)
- This allows handling cases where live price is unavailable

---

#### **Lines 51-66: State Management & Auto-Refresh**
```typescript
export default function PaperTrading() {
  // React state hooks
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();                                  // Initial fetch
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);         // Cleanup on unmount
  }, []);
```

**🔄 Auto-Refresh Logic:**
- Initial data fetch on page load
- **Auto-refresh every 30 seconds** using `setInterval`
- Cleanup interval when component unmounts (prevents memory leaks)

---

#### **Lines 67-90: API Calls - Parallel Fetching**
```typescript
const fetchData = async () => {
  try {
    setLoading(true);
    
    // **PARALLEL API CALLS** - Fetch 4 endpoints simultaneously
    const [portfolioRes, positionsRes, ordersRes, statsRes] = await Promise.all([
      fetch('http://localhost:8000/api/paper-trading/portfolio'),   // Portfolio summary
      fetch('http://localhost:8000/api/paper-trading/positions'),   // All positions
      fetch('http://localhost:8000/api/paper-trading/orders?limit=10'), // Recent orders
      fetch('http://localhost:8000/api/paper-trading/stats')        // Trading stats
    ]);

    // Parse responses
    if (portfolioRes.ok) setPortfolio(await portfolioRes.json());
    if (positionsRes.ok) setPositions(await positionsRes.json());
    if (ordersRes.ok) setOrders(await ordersRes.json());
    if (statsRes.ok) setStats(await statsRes.json());

    setError(null);
  } catch (err) {
    setError('Failed to fetch data');
    console.error(err);
  } finally {
    setLoading(false);
  }
};
```

**💡 Performance Optimization:**
- Uses `Promise.all()` for **parallel execution** (faster than sequential)
- All 4 API calls happen simultaneously, reducing total wait time
- Graceful error handling - if one API fails, others still work

---

#### **Lines 91-115: Display Formatting**
```typescript
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0    // No decimals (₹1,23,456 not ₹1,23,456.00)
  }).format(value);
};

const formatPercent = (value: number) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;  // +2.50% or -1.25%
};

const formatDateTime = (dateString: string) => {
  const date = new Date(dateString);
  // Format: "13 Mar 2026, 3:25 PM IST" - Zerodha Kite style
  const day = date.getDate();
  const month = date.toLocaleString('en-US', { month: 'short' });
  const year = date.getFullYear();
  const time = date.toLocaleString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
  return `${day} ${month} ${year}, ${time} IST`;
};
```

**🎨 Formatting Rules:**
- Currency: Indian format with ₹ symbol, no decimals
- Percent: Always show sign (+/-) with 2 decimals
- DateTime: Human-readable format matching Zerodha Kite UI

---

#### **Lines 145-230: Positions Table Display**
```typescript
{positions.length > 0 ? (
  <div className="overflow-x-auto">
    <table className="w-full border-collapse">
      <thead>
        <tr className="bg-gray-800">
          <th className="text-left p-3">Symbol</th>
          <th className="text-left p-3">Quantity</th>
          <th className="text-left p-3">Avg Price</th>
          <th className="text-left p-3">Current Price</th>
          <th className="text-left p-3">Invested</th>
          <th className="text-left p-3">Current Value</th>
          <th className="text-left p-3">P&L</th>
          <th className="text-left p-3">P&L %</th>
        </tr>
      </thead>
      <tbody>
        {positions.map((pos) => (
          <tr key={pos.id} className="border-b border-gray-800 hover:bg-gray-800/50">
            <td className="p-3"><strong>{pos.symbol}</strong></td>
            <td className="p-3">{pos.quantity}</td>
            <td className="p-3">{formatCurrency(pos.avg_price)}</td>
            
            {/* **NULL HANDLING** - Shows '-' if price unavailable */}
            <td className="p-3">
              {pos.current_price ? formatCurrency(pos.current_price) : '-'}
            </td>
            
            <td className="p-3">{formatCurrency(pos.invested_value)}</td>
            
            {/* **NULL HANDLING** - Shows '-' if value unavailable */}
            <td className="p-3">
              {pos.current_value ? formatCurrency(pos.current_value) : '-'}
            </td>
            
            {/* **COLOR CODING** - Green for profit, red for loss */}
            <td className={`p-3 ${pos.pnl && pos.pnl >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
              {pos.pnl ? formatCurrency(pos.pnl) : '-'}
            </td>
            
            <td className={`p-3 ${pos.pnl_percent && pos.pnl_percent >= 0 ? 'text-bull-green' : 'text-bear-red'}`}>
              {pos.pnl_percent ? formatPercent(pos.pnl_percent) : '-'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
) : (
  <div className="text-center text-gray-400 py-8">No open positions</div>
)}
```

**✅ Proper NULL Handling:**
- If `current_price` is `null` → Display `-` (not ₹0.00)
- If `pnl` is `null` → Display `-` (not showing wrong numbers)
- This matches the backend fix we applied (returning None instead of 0)

---

### 2️⃣ API LAYER - Request Routing

**File:** `services/api/routers/paper_trading.py`

#### **Lines 1-20: Imports & Setup**
```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta

from config.database import get_db
from services.paper_trading.virtual_portfolio import VirtualPortfolio
from pydantic import BaseModel

router = APIRouter(prefix="/api/paper-trading", tags=["paper-trading"])
```

**🔧 Framework:**
- **FastAPI** for REST API endpoints
- **Pydantic** for request/response models (automatic validation)
- **Router pattern** for modular endpoint organization

---

#### **Lines 68-92: Portfolio Instance Management**
```python
# **CACHED INSTANCE** - Reuse connection across requests
_portfolio_instance = None

def get_portfolio():
    """Get or create portfolio instance"""
    global _portfolio_instance
    if _portfolio_instance is None:
        _portfolio_instance = VirtualPortfolio()
    return _portfolio_instance
```

**⚡ Performance Optimization:**
- Portfolio instance is **cached globally**
- Database connection is **reused** across API requests
- Avoids creating new connection for each request (expensive)

**⚠️ Trade-off:**
- Faster response times
- But connection stays open (single shared connection)

---

#### **Lines 94-107: GET /portfolio Endpoint**
```python
@router.get("/portfolio", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """Get paper trading portfolio summary"""
    portfolio = get_portfolio()           # Get cached instance
    summary = portfolio.get_portfolio_summary()  # Query database
    
    if not summary:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return summary  # FastAPI auto-converts dict → JSON
```

**🔄 Request Flow:**
1. Frontend calls: `GET http://localhost:8000/api/paper-trading/portfolio`
2. FastAPI router matches endpoint
3. Gets cached portfolio instance
4. Calls `get_portfolio_summary()` method
5. Returns JSON response

---

#### **Lines 110-117: GET /positions Endpoint**
```python
@router.get("/positions", response_model=List[Position])
async def get_positions():
    """Get all current positions"""
    portfolio = get_portfolio()
    positions = portfolio.get_positions()  # Query database
    return positions  # List of position dictionaries
```

**📊 This is the endpoint the Stock Trading page uses!**
- Called every 30 seconds by frontend
- Returns list of all open positions with live prices
- Response format matches `Position` interface in TypeScript

---

### 3️⃣ PORTFOLIO SERVICE - Database Operations

**File:** `services/paper_trading/virtual_portfolio.py`

#### **Lines 1-45: Connection & Setup**
```python
class VirtualPortfolio:
    """Manages virtual trading portfolio"""
    
    def __init__(self, initial_capital: float = 1000000):
        """
        Initialize virtual portfolio
        
        Args:
            initial_capital: Starting capital in INR (default: 10 lakhs)
        """
        self.initial_capital = initial_capital
        self.conn = self._get_db_connection()  # Persistent connection
        self._ensure_tables()                   # Create tables if needed
        self._initialize_portfolio()            # Set starting capital
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=settings.DB_HOST,    # From .env
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
```

**🔐 Connection Management:**
- Uses **psycopg2** (PostgreSQL driver)
- Connection created once and **reused** (stored in `self.conn`)
- Settings loaded from environment variables (`.env` file)

---

#### **Lines 46-98: Database Schema**
```python
def _ensure_tables(self):
    """Create paper trading tables if they don't exist"""
    cursor = self.conn.cursor()
    
    # **TABLE 1: paper_portfolio** - Portfolio summary
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id SERIAL PRIMARY KEY,
            total_capital DECIMAL(15, 2) NOT NULL,     -- Starting + realized P&L
            available_cash DECIMAL(15, 2) NOT NULL,    -- Cash for new trades
            invested_amount DECIMAL(15, 2) DEFAULT 0,  -- Locked in positions
            total_pnl DECIMAL(15, 2) DEFAULT 0,        -- Total profit/loss
            today_pnl DECIMAL(15, 2) DEFAULT 0,        -- Today's P&L
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # **TABLE 2: paper_positions** - Individual positions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_positions (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(50) NOT NULL,
            quantity INTEGER NOT NULL,                  -- Number of shares
            avg_price DECIMAL(10, 2) NOT NULL,         -- Average entry price
            current_price DECIMAL(10, 2),              -- ✅ NULLABLE - live price
            invested_value DECIMAL(15, 2) NOT NULL,    -- Total invested
            current_value DECIMAL(15, 2),              -- ✅ NULLABLE - current worth
            pnl DECIMAL(15, 2),                        -- ✅ NULLABLE - profit/loss
            pnl_percent DECIMAL(8, 2),                 -- ✅ NULLABLE - P&L percentage
            position_type VARCHAR(10) DEFAULT 'LONG',
            opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol)  -- One position per symbol
        )
    """)
    
    # **TABLE 3: paper_orders** - Order history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_orders (
            id SERIAL PRIMARY KEY,
            order_id VARCHAR(50) UNIQUE NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            order_type VARCHAR(10) NOT NULL,           -- "BUY" or "SELL"
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2),
            executed_price DECIMAL(10, 2),
            status VARCHAR(20) DEFAULT 'PENDING',
            signal_id INTEGER,                         -- Links to signals table
            placed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            executed_at TIMESTAMPTZ,
            reason TEXT
        )
    """)
    
    self.conn.commit()
```

**🗄️ Schema Design:**
- **paper_portfolio:** Single row with portfolio-level data
- **paper_positions:** One row per stock symbol (UNIQUE constraint)
- **paper_orders:** Order history (every BUY/SELL)

**✅ NULL Handling (Fixed):**
- `current_price`, `current_value`, `pnl` columns are **NULLABLE**
- When price unavailable, they stay NULL (not 0)
- Frontend displays `-` instead of ₹0.00

---

#### **Lines 130-165: GET Positions - Database Query**
```python
def get_positions(self) -> List[Dict]:
    """Get all current positions"""
    cursor = self.conn.cursor()
    
    # **SQL QUERY** - Select all open positions
    cursor.execute("""
        SELECT id, symbol, quantity, avg_price, current_price,
               invested_value, current_value, pnl, pnl_percent,
               position_type, opened_at, updated_at
        FROM paper_positions
        WHERE quantity > 0           -- Only open positions
        ORDER BY pnl DESC            -- Best performers first
    """)
    
    positions = []
    for row in cursor.fetchall():
        positions.append({
            'id': row[0],
            'symbol': row[1],
            'quantity': row[2],
            'avg_price': float(row[3]),
            
            # **NULL HANDLING** - Return None if database has NULL
            'current_price': float(row[4]) if row[4] else None,
            
            'invested_value': float(row[5]),
            
            # **FIXED: Returns 0 if NULL** ⚠️ Should return None
            'current_value': float(row[6]) if row[6] else 0,
            'pnl': float(row[7]) if row[7] else 0,
            'pnl_percent': float(row[8]) if row[8] else 0,
            
            'position_type': row[9],
            'opened_at': row[10],
            'updated_at': row[11]
        })
    
    cursor.close()
    return positions
```

**⚠️ ISSUE FOUND (Lines 177-179):**
```python
# CURRENT CODE:
'current_value': float(row[6]) if row[6] else 0,  # ❌ Returns 0
'pnl': float(row[7]) if row[7] else 0,            # ❌ Returns 0
'pnl_percent': float(row[8]) if row[8] else 0,    # ❌ Returns 0

# SHOULD BE:
'current_value': float(row[6]) if row[6] else None,  # ✅ Returns None
'pnl': float(row[7]) if row[7] else None,            # ✅ Returns None
'pnl_percent': float(row[8]) if row[8] else None,    # ✅ Returns None
```

**🐛 This is a remaining fallback issue!** Frontend expects nullable values, but backend returns 0.

---

#### **Lines 185-250: Place Order - BUY Logic**
```python
def place_order(self, order_id: str, symbol: str, order_type: str, 
                quantity: int, price: float, signal_id: int = None) -> bool:
    """Place a virtual order"""
    cursor = self.conn.cursor()
    
    try:
        # **STEP 1: Check available cash for BUY orders**
        if order_type == 'BUY':
            required_amount = quantity * price
            
            cursor.execute("SELECT available_cash FROM paper_portfolio ORDER BY id DESC LIMIT 1")
            available_cash = float(cursor.fetchone()[0])
            
            if required_amount > available_cash:
                logger.warning(f"Insufficient funds: Need ₹{required_amount:,.2f}, Have ₹{available_cash:,.2f}")
                return False  # ❌ Order rejected
        
        # **STEP 2: Insert order record**
        cursor.execute("""
            INSERT INTO paper_orders 
            (order_id, symbol, order_type, quantity, price, executed_price, 
             status, signal_id, executed_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'EXECUTED', %s, %s)
        """, (order_id, symbol, order_type, quantity, price, price, 
              signal_id, datetime.now(timezone.utc)))
        
        # **STEP 3: Update position**
        if order_type == 'BUY':
            self._add_to_position(cursor, symbol, quantity, price)
            self._update_signal_status(cursor, symbol, signal_id)
        else:
            self._reduce_from_position(cursor, symbol, quantity, price)
        
        self.conn.commit()  # ✅ Commit transaction
        logger.info(f"Order executed: {order_type} {quantity} {symbol} @ Rs.{price:.2f}")
        return True
        
    except Exception as e:
        self.conn.rollback()  # ❌ Rollback on error
        logger.error(f"Error placing order: {e}")
        return False
```

**💰 Transaction Flow (BUY Order):**
1. Check if enough cash available
2. Insert order into `paper_orders` table
3. Update or create position in `paper_positions`
4. Deduct cash from `paper_portfolio`
5. Update signal status from PENDING → ACTIVE
6. Commit all changes atomically

---

#### **Lines 265-305: Add to Position**
```python
def _add_to_position(self, cursor, symbol: str, quantity: int, price: float):
    """Add to existing position or create new"""
    
    # **CHECK IF POSITION EXISTS**
    cursor.execute("""
        SELECT quantity, avg_price, invested_value 
        FROM paper_positions 
        WHERE symbol = %s
    """, (symbol,))
    
    existing = cursor.fetchone()
    
    if existing:
        # **SCENARIO 1: Add to existing position**
        old_qty = existing[0]
        old_avg = float(existing[1])
        old_invested = float(existing[2])
        
        new_qty = old_qty + quantity
        new_invested = old_invested + (quantity * price)
        new_avg = new_invested / new_qty  # **Weighted average price**
        
        cursor.execute("""
            UPDATE paper_positions
            SET quantity = %s,
                avg_price = %s,
                invested_value = %s,
                updated_at = %s
            WHERE symbol = %s
        """, (new_qty, new_avg, new_invested, datetime.now(timezone.utc), symbol))
    else:
        # **SCENARIO 2: Create new position**
        invested = quantity * price
        cursor.execute("""
            INSERT INTO paper_positions 
            (symbol, quantity, avg_price, invested_value)
            VALUES (%s, %s, %s, %s)
        """, (symbol, quantity, price, invested))
    
    # **UPDATE PORTFOLIO CASH**
    amount = quantity * price
    cursor.execute("""
        UPDATE paper_portfolio
        SET available_cash = available_cash - %s,    -- Deduct cash
            invested_amount = invested_amount + %s,  -- Add to invested
            updated_at = %s
    """, (amount, amount, datetime.now(timezone.utc)))
```

**📐 Average Price Calculation:**
- **Example:** Buy 10 @ ₹100, then buy 5 @ ₹110
  - Total qty: 15
  - Total invested: ₹1000 + ₹550 = ₹1550
  - New avg: ₹1550 / 15 = **₹103.33**

---

#### **Lines 374-420: Update with Live Prices**
```python
def update_positions_with_live_prices(self, live_prices: Dict[str, float]):
    """
    Update all positions with current market prices
    
    Args:
        live_prices: Dict of {symbol: current_price} from Zerodha
    """
    cursor = self.conn.cursor()
    
    try:
        total_pnl = 0
        
        # **UPDATE EACH POSITION**
        for symbol, current_price in live_prices.items():
            cursor.execute("""
                UPDATE paper_positions
                SET 
                    current_price = %s,                          -- Store live price
                    current_value = quantity * %s,               -- Calculate value
                    pnl = (quantity * %s) - invested_value,      -- Calculate P&L
                    pnl_percent = ((quantity * %s - invested_value) / invested_value * 100),
                    updated_at = %s
                WHERE symbol = %s AND quantity > 0
            """, (current_price, current_price, current_price, current_price, 
                  datetime.now(timezone.utc), symbol))
        
        # **CALCULATE TOTAL UNREALIZED P&L**
        cursor.execute("""
            SELECT COALESCE(SUM(pnl), 0)   -- Sum all position P&Ls
            FROM paper_positions 
            WHERE quantity > 0
        """)
        unrealized_pnl = float(cursor.fetchone()[0])
        
        # **UPDATE PORTFOLIO TIMESTAMP**
        cursor.execute("""
            UPDATE paper_portfolio
            SET updated_at = %s
            WHERE id = (SELECT id FROM paper_portfolio ORDER BY id DESC LIMIT 1)
        """, (datetime.now(timezone.utc),))
        
        self.conn.commit()  # ✅ Save all updates
        logger.debug(f"Updated {len(live_prices)} positions. Unrealized P&L: ₹{unrealized_pnl:,.2f}")
        
    except Exception as e:
        self.conn.rollback()
        logger.error(f"Error updating positions: {e}")
```

**🔄 Price Update SQL:**
```sql
UPDATE paper_positions
SET 
    current_price = 150.50,                    -- Live price from Zerodha
    current_value = quantity * 150.50,         -- 100 shares × ₹150.50 = ₹15,050
    pnl = (quantity * 150.50) - invested_value, -- ₹15,050 - ₹14,000 = +₹1,050
    pnl_percent = ((quantity * 150.50 - invested_value) / invested_value * 100), -- +7.5%
    updated_at = CURRENT_TIMESTAMP
WHERE symbol = 'INFY' AND quantity > 0
```

**💡 This SQL runs every 60 seconds during market hours!**

---

### 4️⃣ TRADING ENGINE - Live Price Updates

**File:** `services/paper_trading/paper_trading_engine.py`

#### **Lines 20-40: Engine Initialization**
```python
class PaperTradingEngine:
    """Main paper trading engine with live market data"""
    
    def __init__(self, auto_execute: bool = True):
        """Initialize paper trading engine"""
        self.portfolio = VirtualPortfolio()          # Portfolio manager
        self.risk_manager = RiskManager()            # Risk validation
        self.zerodha = ZerodhaAdapter()              # Market data source
        self.auto_execute = auto_execute             # Auto-execute signals?
        self.watchlist = ['INFY', 'RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK']
        self.running = False
        
        logger.info("Paper Trading Engine initialized with Risk Manager")
```

**🎯 Components:**
- **VirtualPortfolio:** Database operations
- **RiskManager:** Position sizing, stop-loss validation
- **ZerodhaAdapter:** Live market data API
- **Watchlist:** Default stocks to monitor

---

#### **Lines 42-70: Fetch Live Prices from Zerodha**
```python
def get_live_prices(self, symbols: List[str] = None) -> Dict[str, float]:
    """
    Fetch live prices from Zerodha
    
    Args:
        symbols: List of symbols to fetch (defaults to watchlist)
    """
    if symbols is None:
        symbols = self.watchlist
    
    try:
        prices = {}
        
        # **ZERODHA API CALL** - Get Last Traded Price
        for symbol in symbols:
            instruments = self.zerodha.kite.ltp([f"NSE:{symbol}"])
            
            if instruments:
                key = f"NSE:{symbol}"
                if key in instruments:
                    prices[symbol] = instruments[key]['last_price']
        
        logger.debug(f"Fetched live prices: {prices}")
        return prices  # {'INFY': 1450.50, 'TCS': 3200.25, ...}
        
    except Exception as e:
        logger.error(f"Error fetching live prices: {e}")
        return {}  # Return empty dict on error
```

**📡 Zerodha API Integration:**
- Calls `kite.ltp()` method (Last Traded Price)
- Input: `["NSE:INFY", "NSE:TCS", ...]`
- Output: `{"NSE:INFY": {"last_price": 1450.50}, ...}`
- Returns dict mapping symbol → price

---

#### **Lines 238-249: Update Portfolio Prices**
```python
def update_portfolio_prices(self):
    """Update all portfolio positions with live prices"""
    positions = self.portfolio.get_positions()  # Get open positions
    
    if not positions:
        return  # No positions to update
    
    symbols = [p['symbol'] for p in positions]  # Extract symbols
    live_prices = self.get_live_prices(symbols) # Fetch from Zerodha
    
    if live_prices:
        self.portfolio.update_positions_with_live_prices(live_prices)  # Update DB
```

**🔄 Update Flow:**
1. Get all open positions from database
2. Extract symbol names: `['INFY', 'TCS', 'RELIANCE']`
3. Fetch live prices from Zerodha API
4. Update database with new prices (runs SQL UPDATE)

---

#### **Lines 251-265: Market Hours Check**
```python
def is_market_open(self) -> bool:
    """Check if market is currently open"""
    now = datetime.now()
    
    # **CHECK 1: Skip weekends**
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # **CHECK 2: Market hours: 9:15 AM to 3:30 PM IST**
    market_open = dt_time(9, 15)
    market_close = dt_time(15, 30)
    current_time = now.time()
    
    return market_open <= current_time <= market_close
```

**⏰ Market Hours Logic:**
- Monday-Friday only (weekday 0-4)
- 9:15 AM to 3:30 PM IST
- Returns `True` during trading hours, `False` otherwise

---

#### **Lines 266-300: Run Trading Cycle**
```python
def run_cycle(self):
    """Run one trading cycle"""
    try:
        logger.info("=" * 60)
        logger.info("Running paper trading cycle")
        
        # **STEP 1: Update portfolio with live prices**
        self.update_portfolio_prices()
        
        # **STEP 2: Check exit conditions (stop-loss/target)**
        self.check_exit_conditions()
        
        # **STEP 3: Execute pending signals (if auto-execute enabled)**
        if self.auto_execute:
            signals = self.get_pending_signals()
            
            if signals:
                logger.info(f"Found {len(signals)} pending signals")
                
                for signal in signals:
                    symbol = signal['symbol']
                    
                    # Get current price
                    prices = self.get_live_prices([symbol])
                    current_price = prices.get(symbol)
                    
                    if current_price:
                        # Check if price is close to signal entry (within 2%)
                        entry_price = signal['entry_price']
                        price_diff_pct = abs(current_price - entry_price) / entry_price * 100
                        
                        if price_diff_pct <= 2:
                            self.execute_signal(signal, current_price)
                        else:
                            logger.debug(f"Skipping {symbol}: Price moved {price_diff_pct:.2f}% from signal")
        
        # **STEP 4: Display portfolio summary**
        summary = self.portfolio.get_portfolio_summary()
        logger.info(f"""
Portfolio Summary:
   Total Capital: Rs.{summary['total_capital']:,.2f}
   Available Cash: Rs.{summary['available_cash']:,.2f}
   Invested: Rs.{summary['invested_amount']:,.2f}
   Total P&L: Rs.{summary['total_pnl']:,.2f}
   Today P&L: Rs.{summary['today_pnl']:,.2f}
   Positions: {summary['positions_count']}
        """)
        
    except Exception as e:
        logger.error(f"Error in trading cycle: {e}")
```

**🔄 Trading Cycle (Every 60 seconds):**
1. **Update prices** from Zerodha API → Database
2. **Check exits** (stop-loss/target hit?)
3. **Execute signals** (auto-buy new positions)
4. **Log summary** to terminal

---

#### **Lines 318-345: Main Loop**
```python
def start(self, interval: int = 60):
    """
    Start paper trading engine
    
    Args:
        interval: Update interval in seconds (default: 60)
    """
    self.running = True
    logger.info(f"Paper Trading Engine started (interval: {interval}s)")
    
    try:
        while self.running:
            # **CHECK MARKET HOURS**
            if self.is_market_open():
                logger.info("Market is OPEN")
                self.run_cycle()  # Execute trading cycle
            else:
                logger.info("Market is CLOSED - Skipping cycle")
            
            # **SLEEP UNTIL NEXT CYCLE**
            time.sleep(interval)  # Default: 60 seconds
            
    except KeyboardInterrupt:
        logger.info("Stopping paper trading engine...")
        self.stop()
```

**♾️ Infinite Loop:**
- Runs continuously while `self.running = True`
- Checks market hours before each cycle
- Sleeps 60 seconds between cycles
- Can be stopped with Ctrl+C

---

### 5️⃣ SIGNAL GENERATION - How Signals Get Created

**File:** `generate_nifty50_signals.py`

#### **Lines 1-45: Setup & Stock List**
```python
import psycopg2
from datetime import datetime, timedelta
from config.settings import get_settings
from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter

settings = get_settings()

# **Top Nifty 50 stocks for paper trading**
NIFTY_50_STOCKS = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'HINDUNILVR', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
    'LT', 'AXISBANK', 'WIPRO', 'HCLTECH', 'ASIANPAINT',
    'MARUTI', 'SUNPHARMA', 'TITAN', 'BAJFINANCE', 'ULTRACEMCO'
]

def generate_sample_signals():
    """Generate BUY signals for Nifty 50 stocks using live market data"""
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = conn.cursor()
    
    # Initialize Zerodha adapter for live prices
    print("Connecting to Zerodha for live prices...")
    zerodha = ZerodhaAdapter()
    
    if not zerodha.kite:
        print("ERROR: Zerodha connection failed. Please check your access token.")
        print("Run: py generate_token_quick.py")
        return
```

**🎯 Signal Generation Process:**
1. Connect to database
2. Initialize Zerodha adapter
3. Fetch live quotes for all 20 stocks
4. Generate BUY signals with entry/target/stop-loss
5. Insert into `signals` table

---

#### **Lines 47-75: Fetch Live Quotes**
```python
signals_created = 0

# **FETCH ALL QUOTES AT ONCE** (More efficient than one-by-one)
try:
    instruments = [f"NSE:{symbol}" for symbol in NIFTY_50_STOCKS]
    quotes = zerodha.kite.quote(instruments)  # Batch API call
    print(f"✅ Fetched live prices for {len(quotes)} stocks\n")
except Exception as e:
    print(f"ERROR fetching quotes: {e}")
    return

for symbol in NIFTY_50_STOCKS:
    instrument_key = f"NSE:{symbol}"
    
    if instrument_key not in quotes:
        print(f"⚠️  No data for {symbol}, skipping...")
        continue
    
    quote_data = quotes[instrument_key]
    close_price = quote_data.get('last_price')
    
    # **✅ VALIDATION ADDED** - Skip if price invalid
    if not close_price or close_price <= 0:
        print(f"⚠️  Invalid price for {symbol} (price={close_price}), skipping...")
        continue
```

**⚡ Batch Fetching:**
- Calls `kite.quote()` once for all 20 symbols
- More efficient than 20 separate API calls
- Zerodha returns dict with all quotes

**✅ Price Validation** (Recently Fixed):
- Checks `if not close_price or close_price <= 0`
- Skips stocks with invalid/missing prices
- Prevents inserting bad data into database

---

#### **Lines 76-120: Calculate Signal Parameters**
```python
# **CALCULATE ENTRY/TARGET/STOP-LOSS**
entry_price = float(close_price)
stop_loss = entry_price * 0.98     # 2% stop loss
target_price = entry_price * 1.03  # 3% target

# **CALCULATE CONFIDENCE** based on intraday position
day_high = quote_data.get('ohlc', {}).get('high', entry_price)
day_low = quote_data.get('ohlc', {}).get('low', entry_price)

if day_high > day_low:
    # If price near day's high, higher confidence
    price_position = (entry_price - day_low) / (day_high - day_low)
    confidence = int(70 + (price_position * 10))  # 70-80%
else:
    confidence = 75

# **INSERT SIGNAL INTO DATABASE**
cursor.execute("""
    INSERT INTO signals 
    (timestamp, symbol, strategy, signal_type, timeframe, entry_price, 
     stop_loss, target_price, confidence, quantity, reason, status, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    datetime.now(),
    symbol,
    'MOMENTUM_BREAKOUT',  -- Strategy name
    'BUY',                 -- Signal type
    '15m',                 -- Timeframe
    entry_price,
    stop_loss,
    target_price,
    confidence,            -- 70-80% based on analysis
    0,                     -- Quantity calculated later by engine
    f'Strong momentum detected at Rs.{entry_price:.2f} (Day High: Rs.{day_high:.2f})',
    'PENDING',             -- Initial status
    datetime.now()
))

signals_created += 1
print(f"✅ {symbol:12} BUY | Entry: Rs.{entry_price:8,.2f} | Target: Rs.{target_price:8,.2f} | SL: Rs.{stop_loss:8,.2f} | {confidence}%")

conn.commit()  # ✅ Save all signals
```

**📊 Signal Example:**
```
Symbol: INFY
Entry: ₹1,450.50
Target: ₹1,493.50 (+3%)
Stop Loss: ₹1,421.50 (-2%)
Confidence: 78%
Status: PENDING
```

---

### 6️⃣ ZERODHA ADAPTER - Live Market Data

**File:** `services/market_data/adapters/zerodha_adapter.py`

#### **Key API Calls:**
```python
# Get Last Traded Price (LTP)
instruments = kite.ltp(["NSE:INFY", "NSE:TCS"])
# Returns: {"NSE:INFY": {"last_price": 1450.50, "last_trade_time": "..."},...}

# Get Full Quote (OHLCV + more data)
quotes = kite.quote(["NSE:INFY"])
# Returns: {
#   "NSE:INFY": {
#     "last_price": 1450.50,
#     "ohlc": {"open": 1440, "high": 1455, "low": 1438, "close": 1448},
#     "volume": 1234567,
#     "average_price": 1445.20,
#     ...
#   }
# }
```

**🔐 Authentication:**
- Uses access token from `.env` file
- Token valid for 24 hours
- Must refresh daily using `generate_token_quick.py`

---

## 🔄 Complete End-to-End Flow

### **How a Stock Position Gets to Your Screen:**

#### **STEP 1: Generate Signal (Manual)**
```bash
# Run: py generate_nifty50_signals.py
```
1. Fetches live prices from Zerodha
2. Calculates entry, target, stop-loss
3. **Inserts into `signals` table** with status=PENDING

**Database State:**
```sql
signals table:
| id | symbol | signal_type | entry_price | status  |
|----|--------|-------------|-------------|---------|
| 1  | INFY   | BUY         | 1450.50     | PENDING |
```

---

#### **STEP 2: Start Paper Trading Engine (Background Process)**
```bash
# Run: py start_paper_trading.py
```
1. Engine starts infinite loop
2. Every 60 seconds:
   - Checks if market is open
   - Runs trading cycle

---

#### **STEP 3: Trading Cycle Execution (Every 60s)**

**Sub-step 3.1: Get Pending Signals**
```python
# paper_trading_engine.py - get_pending_signals()
cursor.execute("""
    SELECT s.id, s.symbol, s.signal_type, s.entry_price, 
           s.stop_loss, s.target_price, s.confidence, s.strategy
    FROM signals s
    LEFT JOIN paper_orders po ON s.id = po.signal_id
    WHERE po.signal_id IS NULL        -- Not yet executed
      AND s.timestamp >= CURRENT_DATE - INTERVAL '7 days'
      AND s.confidence >= 70          -- Min confidence threshold
    ORDER BY s.confidence DESC
    LIMIT 10
""")
```

**📋 Query Logic:**
- Find signals NOT yet in `paper_orders` (using LEFT JOIN)
- Only last 7 days
- Only high confidence (≥70%)
- Best signals first

---

**Sub-step 3.2: Execute Signal**
```python
# Get current price
prices = self.get_live_prices([symbol])  # Zerodha API call
current_price = prices.get(symbol)

# Check if price close to entry (within 2%)
entry_price = signal['entry_price']
price_diff_pct = abs(current_price - entry_price) / entry_price * 100

if price_diff_pct <= 2:
    self.execute_signal(signal, current_price)  # Place BUY order
```

**💰 Order Execution:**
1. Fetch current price from Zerodha
2. Validate price hasn't moved too much (±2% from entry)
3. Calculate position size using RiskManager
4. Place BUY order
5. Insert into `paper_orders` table
6. Update/create position in `paper_positions`
7. Deduct cash from `paper_portfolio`
8. Update signal status PENDING → ACTIVE

**Database State After Execution:**
```sql
paper_orders table:
| order_id      | symbol | order_type | quantity | executed_price | status   |
|---------------|--------|------------|----------|----------------|----------|
| PAPER_INFY_.. | INFY   | BUY        | 150      | 1450.50        | EXECUTED |

paper_positions table:
| id | symbol | quantity | avg_price | current_price | invested_value | current_value | pnl  | pnl_percent |
|----|--------|----------|-----------|---------------|----------------|---------------|------|-------------|
| 1  | INFY   | 150      | 1450.50   | NULL          | 217575.00      | NULL          | NULL | NULL        |

signals table:
| id | symbol | signal_type | status | 
|----|--------|-------------|--------|
| 1  | INFY   | BUY         | ACTIVE |  ← Status updated
```

**Note:** `current_price`, `pnl` are NULL initially - will be updated in next price update cycle.

---

**Sub-step 3.3: Update Prices**
```python
# paper_trading_engine.py - update_portfolio_prices()
positions = self.portfolio.get_positions()  # Get all positions
symbols = [p['symbol'] for p in positions]  # ['INFY', 'TCS', ...]

# Fetch live prices from Zerodha
live_prices = self.get_live_prices(symbols)  
# Returns: {'INFY': 1455.75, 'TCS': 3205.50, ...}

# Update database
self.portfolio.update_positions_with_live_prices(live_prices)
```

**SQL Executed:**
```sql
UPDATE paper_positions
SET 
    current_price = 1455.75,
    current_value = quantity * 1455.75,        -- 150 × 1455.75 = 218,362.50
    pnl = (quantity * 1455.75) - invested_value, -- 218,362.50 - 217,575 = +787.50
    pnl_percent = ((quantity * 1455.75 - invested_value) / invested_value * 100), -- +0.36%
    updated_at = CURRENT_TIMESTAMP
WHERE symbol = 'INFY' AND quantity > 0
```

**Database State After Price Update:**
```sql
paper_positions table:
| id | symbol | quantity | avg_price | current_price | invested_value | current_value | pnl     | pnl_percent |
|----|--------|----------|-----------|---------------|----------------|---------------|---------|-------------|
| 1  | INFY   | 150      | 1450.50   | 1455.75       | 217575.00      | 218362.50     | +787.50 | +0.36       |
```

---

**Sub-step 3.4: Check Exit Conditions**
```python
# paper_trading_engine.py - check_exit_conditions()
for position in positions:
    current_price = live_prices.get(symbol)
    avg_price = position['avg_price']
    
    # Use RiskManager to check if should exit
    should_exit, reason = self.risk_manager.should_exit_position(
        symbol=symbol,
        entry_price=avg_price,
        current_price=current_price,
        is_options=False
    )
    
    if should_exit:
        # **AUTO-SELL** if stop-loss or target hit
        self.portfolio.place_order(
            order_id=f"PAPER_EXIT_{symbol}_...",
            symbol=symbol,
            order_type='SELL',
            quantity=position['quantity'],
            price=current_price
        )
        logger.info(f"🔔 Exited {symbol}: {reason}")
```

**🛡️ Exit Logic (RiskManager):**
- **Stop-Loss:** If price drops 2% below entry → AUTO-SELL
- **Target:** If price rises 3% above entry → AUTO-SELL
- **For Options:** Stop-loss is 40% (wider tolerance)

---

#### **STEP 4: Frontend Auto-Refresh (Every 30s)**

**Frontend Loop:**
```typescript
// paper-trading.tsx - useEffect hook
useEffect(() => {
    fetchData();                                  // Initial load
    const interval = setInterval(fetchData, 30000); // Every 30s
    return () => clearInterval(interval);
}, []);

const fetchData = async () => {
    // Call API endpoint
    const positionsRes = await fetch('http://localhost:8000/api/paper-trading/positions');
    if (positionsRes.ok) setPositions(await positionsRes.json());
    // ... other endpoints
};
```

**🔄 Auto-Refresh:**
- Frontend refreshes **every 30 seconds**
- Backend updates prices **every 60 seconds**
- User sees updates within 30-60 seconds of price change

---

#### **STEP 5: API Returns Data**

**API Endpoint:**
```python
# routers/paper_trading.py
@router.get("/positions", response_model=List[Position])
async def get_positions():
    portfolio = get_portfolio()       # Cached instance
    positions = portfolio.get_positions()  # Query DB
    return positions  # Auto-converted to JSON by FastAPI
```

**JSON Response Example:**
```json
[
  {
    "id": 1,
    "symbol": "INFY",
    "quantity": 150,
    "avg_price": 1450.50,
    "current_price": 1455.75,
    "invested_value": 217575.00,
    "current_value": 218362.50,
    "pnl": 787.50,
    "pnl_percent": 0.36,
    "position_type": "LONG",
    "opened_at": "2026-03-14T09:20:15Z",
    "updated_at": "2026-03-14T10:15:30Z"
  }
]
```

---

#### **STEP 6: Frontend Displays Data**

**TypeScript Rendering:**
```typescript
{positions.map((pos) => (
  <tr key={pos.id}>
    <td>{pos.symbol}</td>                      {/* INFY */}
    <td>{pos.quantity}</td>                    {/* 150 */}
    <td>{formatCurrency(pos.avg_price)}</td>   {/* ₹1,451 */}
    <td>{pos.current_price ? formatCurrency(pos.current_price) : '-'}</td>  {/* ₹1,456 */}
    <td>{formatCurrency(pos.invested_value)}</td>  {/* ₹2,17,575 */}
    <td>{pos.current_value ? formatCurrency(pos.current_value) : '-'}</td>  {/* ₹2,18,363 */}
    
    {/* Color-coded P&L */}
    <td className={pos.pnl >= 0 ? 'text-green' : 'text-red'}>
      {pos.pnl ? formatCurrency(pos.pnl) : '-'}  {/* +₹788 in green */}
    </td>
    
    <td className={pos.pnl_percent >= 0 ? 'text-green' : 'text-red'}>
      {pos.pnl_percent ? formatPercent(pos.pnl_percent) : '-'}  {/* +0.36% in green */}
    </td>
  </tr>
))}
```

**🎨 User Sees:**
| Symbol | Qty | Avg Price | Current Price | Invested | Current Value | P&L      | P&L %   |
|--------|-----|-----------|---------------|----------|---------------|----------|---------|
| INFY   | 150 | ₹1,451    | ₹1,456        | ₹2,17,575| ₹2,18,363     | **+₹788**  | **+0.36%** |

---

## 🗄️ Database Schema Details

### **Table 1: signals**
```sql
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    strategy VARCHAR(50),                -- "MOMENTUM_BREAKOUT", "VWAP_TRAP"
    signal_type VARCHAR(10) NOT NULL,    -- "BUY" or "SELL"
    timeframe VARCHAR(10),               -- "5m", "15m", "1h"
    entry_price DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    target_price DECIMAL(10, 2),
    confidence DECIMAL(5, 2),            -- 70-95%
    quantity INTEGER DEFAULT 0,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING → ACTIVE → CLOSED
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**Status Flow:**
- **PENDING:** Signal created, not yet executed
- **ACTIVE:** Position opened, monitoring for exit
- **CLOSED:** Position exited (target/stop-loss hit)

---

### **Table 2: paper_orders**
```sql
CREATE TABLE paper_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,  -- "PAPER_INFY_1710401234"
    symbol VARCHAR(50) NOT NULL,
    order_type VARCHAR(10) NOT NULL,       -- "BUY" or "SELL"
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2),                  -- Order price
    executed_price DECIMAL(10, 2),         -- Actual execution price
    status VARCHAR(20) DEFAULT 'PENDING',
    signal_id INTEGER,                     -- Foreign key to signals.id
    placed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMPTZ,
    reason TEXT
);
```

**Order History:**
- Every BUY/SELL creates a new row
- Links to signal via `signal_id`
- Tracks execution timestamp
- Used for order history display

---

### **Table 3: paper_positions**
```sql
CREATE TABLE paper_positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(10, 2) NOT NULL,
    current_price DECIMAL(10, 2),          -- ✅ NULLABLE - Updated every 60s
    invested_value DECIMAL(15, 2) NOT NULL,
    current_value DECIMAL(15, 2),          -- ✅ NULLABLE - Calculated from price
    pnl DECIMAL(15, 2),                    -- ✅ NULLABLE - current - invested
    pnl_percent DECIMAL(8, 2),             -- ✅ NULLABLE - (pnl/invested) * 100
    position_type VARCHAR(10) DEFAULT 'LONG',
    opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol)                         -- Only one position per symbol
);
```

**Position Lifecycle:**
1. **New Position:** Created with `current_price=NULL`
2. **Price Update:** Updated every 60s with live price
3. **Partial Sale:** `quantity` reduced, `avg_price` stays same
4. **Full Exit:** Row deleted

---

### **Table 4: paper_portfolio**
```sql
CREATE TABLE paper_portfolio (
    id SERIAL PRIMARY KEY,
    total_capital DECIMAL(15, 2) NOT NULL,   -- Initial + realized P&L
    available_cash DECIMAL(15, 2) NOT NULL,  -- Cash for trading
    invested_amount DECIMAL(15, 2) DEFAULT 0, -- Sum of open positions
    total_pnl DECIMAL(15, 2) DEFAULT 0,      -- Unrealized + realized
    today_pnl DECIMAL(15, 2) DEFAULT 0,      -- Since market open
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**Single Row Design:**
- Only one row in table (portfolio summary)
- Updated on every BUY/SELL transaction
- `available_cash` reduced on BUY, increased on SELL

---

## ⏱️ Timeline Example

```
T+0:00  User runs: py generate_nifty50_signals.py
        → 20 signals inserted with status=PENDING
        → Database: signals table populated

T+0:10  User runs: py start_paper_trading.py
        → Engine starts background loop
        → Checking market hours...

T+0:10  [Cycle 1] Market is OPEN
        → Fetch pending signals (20 found)
        → Get live prices from Zerodha
        → Signal: INFY BUY @ ₹1,450.50 (confidence 78%)
        → Calculate position size: 150 shares (₹2,17,575)
        → Execute BUY order
        → INSERT into paper_orders
        → INSERT into paper_positions (current_price=NULL initially)
        → UPDATE paper_portfolio (available_cash reduced)
        → UPDATE signals (status=ACTIVE)

T+1:10  [Cycle 2] Update prices
        → Fetch live prices: INFY = ₹1,455.75
        → UPDATE paper_positions SET current_price=1455.75, pnl=+787.50
        → Logger: "Unrealized P&L: ₹787.50"

T+1:15  User opens dashboard (http://localhost:3000/paper-trading)
        → Frontend calls: GET /api/paper-trading/positions
        → API queries: SELECT * FROM paper_positions
        → Returns: [{symbol: "INFY", pnl: 787.50, ...}]
        → Frontend displays: Green "+₹788 (+0.36%)"

T+1:45  [Auto-refresh] Frontend refreshes (30s timer)
        → Calls API again
        → Gets updated prices (if engine ran another cycle)

T+2:10  [Cycle 3] Update prices
        → INFY now ₹1,460.00
        → UPDATE pnl=+1,425.00 (+0.65%)

T+2:15  [Auto-refresh] Frontend shows new P&L
        → User sees: "+₹1,425 (+0.65%)" in green

... Every 60s engine updates prices
... Every 30s frontend refreshes display
```

---

## 🔧 Key Configuration

### **Backend Update Frequency:**
```python
# paper_trading_engine.py - Line 323
engine.start(interval=60)  # Update every 60 seconds
```

### **Frontend Refresh Frequency:**
```typescript
// paper-trading.tsx - Line 62
const interval = setInterval(fetchData, 30000); // Refresh every 30s
```

### **Market Hours:**
```python
# paper_trading_engine.py - Line 254-258
market_open = dt_time(9, 15)   # 9:15 AM IST
market_close = dt_time(15, 30) # 3:30 PM IST
```

### **Risk Parameters:**
```python
# risk_manager.py
MAX_POSITION_SIZE_PCT = 0.20      # Max 20% capital per position
STOP_LOSS_PCT = 0.02              # 2% stop loss for stocks
TARGET_PCT = 0.03                 # 3% target for stocks
OPTIONS_STOP_LOSS_PCT = 0.40      # 40% stop loss for options (wider)
```

---

## 🐛 Issues Found & Fixed

### **Issue 1: Returning 0 Instead of None (FIXED ✅)**

**Problem:** When price unavailable, system returned `0` instead of `None`

**Impact:** Dashboard showed `₹0.00` (looks like valid price) instead of `-` (unavailable)

**Files Fixed:**
- ✅ `options_trading_engine.py` - Returns None for missing premium
- ✅ `zerodha_adapter.py` - Validates LTP before storing
- ✅ `options_indicators.py` - Returns None for support/resistance
- ✅ `options_virtual_portfolio.py` - Skips invalid premiums

**Remaining Issue in Stock Trading:**
```python
# virtual_portfolio.py - Line 177-179
# ⚠️ STILL RETURNS 0 INSTEAD OF NONE
'current_value': float(row[6]) if row[6] else 0,    # Should be None
'pnl': float(row[7]) if row[7] else 0,              # Should be None
'pnl_percent': float(row[8]) if row[8] else 0,      # Should be None
```

**Fix Needed:**
```python
# CORRECT VERSION:
'current_value': float(row[6]) if row[6] else None,
'pnl': float(row[7]) if row[7] else None,
'pnl_percent': float(row[8]) if row[8] else None,
```

---

## 📈 Real-World Example

### **Scenario: Buying INFY Stock**

**T=0: Generate Signal**
```bash
$ py generate_nifty50_signals.py
✅ INFY        BUY | Entry: Rs. 1,450.50 | Target: Rs. 1,493.50 | SL: Rs. 1,421.50 | 78%
```

**Database:**
```sql
INSERT INTO signals VALUES (
    symbol='INFY',
    signal_type='BUY',
    entry_price=1450.50,
    status='PENDING'
)
```

---

**T=10s: Start Engine**
```bash
$ py start_paper_trading.py
🚀 Starting Paper Trading Engine
✅ Engine initialized successfully
⏰ Starting trading loop...
```

**Log Output:**
```
============================================================
Running paper trading cycle
Found 1 pending signals
INFY: Optimal size = 150 shares (Rs.2,17,575.00, 78% confidence)
✅ Executed: BUY 150 INFY @ Rs.1,450.50 (Rs.2,17,575.00, 78% confidence)

Portfolio Summary:
   Total Capital: Rs.10,00,000.00
   Available Cash: Rs.7,82,425.00  ← Reduced by ₹2,17,575
   Invested: Rs.2,17,575.00
   Total P&L: Rs.0.00
   Positions: 1
```

---

**T=70s: First Price Update**
```
Running paper trading cycle
Fetched live prices: {'INFY': 1455.75}
Updated 1 positions. Unrealized P&L: ₹787.50

Portfolio Summary:
   Total P&L: Rs.787.50  ← Profit showing!
```

**Database:**
```sql
UPDATE paper_positions SET
    current_price = 1455.75,
    current_value = 218362.50,
    pnl = 787.50,
    pnl_percent = 0.36
WHERE symbol = 'INFY'
```

---

**T=90s: User Opens Dashboard**

**Browser:** `http://localhost:3000/paper-trading`

**API Call:**
```
GET http://localhost:8000/api/paper-trading/positions
Response: [{"symbol": "INFY", "pnl": 787.50, ...}]
```

**Screen Display:**
```
📊 Stock Paper Trading

Portfolio Summary:
┌─────────────────┬─────────────────┬─────────────┐
│ Total Capital   │ Available Cash  │ Invested    │
│ ₹10,00,000      │ ₹7,82,425       │ ₹2,17,575   │
└─────────────────┴─────────────────┴─────────────┘

Current Positions (1):
┌────────┬─────┬───────┬─────────┬───────────┬───────────┬─────────┬────────┐
│ Symbol │ Qty │ Avg   │ Current │ Invested  │ Current   │ P&L     │ P&L %  │
├────────┼─────┼───────┼─────────┼───────────┼───────────┼─────────┼────────┤
│ INFY   │ 150 │ ₹1,451│ ₹1,456  │ ₹2,17,575 │ ₹2,18,363 │ +₹788   │ +0.36% │ (GREEN)
└────────┴─────┴───────┴─────────┴───────────┴───────────┴─────────┴────────┘
```

---

**T=130s: Price Moves Down to ₹1,422 (Hits Stop-Loss)**

**Engine Log:**
```
Running paper trading cycle
Fetched live prices: {'INFY': 1422.00}
Risk Manager: INFY - Stop-loss triggered (-1.96%)
🔔 Exited INFY: Stop-loss triggered at Rs.1,422.00 (Loss: -1.96%)

SELL 150 INFY @ Rs.1,422.00
Position closed: INFY P&L: Rs.-4,275.00

Portfolio Summary:
   Total Capital: Rs.9,95,725.00  ← Lost ₹4,275
   Available Cash: Rs.9,95,725.00  ← All cash (no positions)
   Invested: Rs.0.00
   Total P&L: Rs.-4,275.00
   Positions: 0
```

**Database:**
```sql
-- Position closed
DELETE FROM paper_positions WHERE symbol = 'INFY'

-- Order recorded
INSERT INTO paper_orders VALUES (
    order_id='PAPER_EXIT_INFY_...',
    symbol='INFY',
    order_type='SELL',
    quantity=150,
    executed_price=1422.00,
    status='EXECUTED'
)

-- Signal updated
UPDATE signals SET status='CLOSED' WHERE symbol='INFY'

-- Portfolio updated
UPDATE paper_portfolio SET
    available_cash = 995725.00,
    invested_amount = 0,
    total_pnl = -4275.00
```

---

**T=150s: User Refreshes Dashboard**

**Screen Now Shows:**
```
Current Positions (0):
┌──────────────────────────────────┐
│ No open positions                │
└──────────────────────────────────┘

Recent Orders:
┌─────────────┬────────┬──────┬─────┬────────┬──────────┐
│ Time        │ Symbol │ Type │ Qty │ Price  │ Status   │
├─────────────┼────────┼──────┼─────┼────────┼──────────┤
│ 10:22:10 AM │ INFY   │ SELL │ 150 │ ₹1,422 │ EXECUTED │ (RED)
│ 10:20:15 AM │ INFY   │ BUY  │ 150 │ ₹1,451 │ EXECUTED │ (GREEN)
└─────────────┴────────┴──────┴─────┴────────┴──────────┘

Portfolio Summary:
Total P&L: -₹4,275 (RED)
```

---

## 🚀 Starting the System

### **Step 1: Generate Signals**
```bash
py generate_nifty50_signals.py
```
**Output:**
```
================================================================================
GENERATING TRADING SIGNALS FOR NIFTY 50 STOCKS
================================================================================

Connecting to Zerodha for live prices...
✅ Fetched live prices for 20 stocks

✅ RELIANCE     BUY | Entry: Rs. 2,450.00 | Target: Rs. 2,523.50 | SL: Rs. 2,401.00 | 75%
✅ TCS          BUY | Entry: Rs. 3,200.50 | Target: Rs. 3,296.50 | SL: Rs. 3,136.50 | 78%
✅ INFY         BUY | Entry: Rs. 1,450.50 | Target: Rs. 1,493.50 | SL: Rs. 1,421.50 | 72%
... (17 more)

================================================================================
✅ CREATED 20 TRADING SIGNALS
================================================================================
Ready for paper trading! Run: py start_paper_trading.py
```

---

### **Step 2: Start Trading Engine**
```bash
py start_paper_trading.py
```
**Output:**
```
============================================================
🚀 Starting Paper Trading Engine
============================================================

Features:
  ✅ Virtual portfolio with ₹10,00,000 capital
  ✅ Live market data from Zerodha
  ✅ Auto-execution of trading signals
  ✅ Real-time position tracking
  ✅ Automatic stop-loss and target management

Settings:
  • Update interval: 60 seconds
  • Risk per trade: 20% max
  • Target: +3% | Stop Loss: -2%
  • Market hours: 9:15 AM - 3:30 PM IST

============================================================

✅ Engine initialized successfully
⏰ Starting trading loop...

[09:15:00] Market is OPEN
[09:15:00] Found 20 pending signals
[09:15:05] INFY: Optimal size = 150 shares (Rs.2,17,575.00, 78% confidence)
[09:15:05] ✅ Executed: BUY 150 INFY @ Rs.1,450.50
[09:16:00] Updated 1 positions. Unrealized P&L: ₹787.50
... (continues every 60s)
```

---

### **Step 3: Start API Server**
```bash
py start_api.py
```
**Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Exposes endpoints:**
- `GET /api/paper-trading/portfolio` - Portfolio summary
- `GET /api/paper-trading/positions` - All positions
- `GET /api/paper-trading/orders` - Order history
- `GET /api/paper-trading/stats` - Trading statistics
- `POST /api/paper-trading/orders` - Place manual order

---

### **Step 4: Open Dashboard**
```
Browser: http://localhost:3000/paper-trading
```

**Frontend automatically:**
1. Fetches data from 4 API endpoints (parallel)
2. Displays positions table
3. Auto-refreshes every 30 seconds
4. Color-codes P&L (green/red)

---

## 🔍 Debugging Tips

### **Check Live Prices:**
```bash
py -c "from services.market_data.adapters.zerodha_adapter import ZerodhaAdapter; z = ZerodhaAdapter(); prices = z.kite.ltp(['NSE:INFY']); print(prices)"
```

### **Check Database Positions:**
```bash
py -c "import psycopg2; from config.settings import get_settings; s = get_settings(); conn = psycopg2.connect(host=s.DB_HOST, port=s.DB_PORT, database=s.DB_NAME, user=s.DB_USER, password=s.DB_PASSWORD); cur = conn.cursor(); cur.execute('SELECT symbol, quantity, avg_price, current_price, pnl FROM paper_positions'); [print(f'{r[0]}: {r[1]} shares @ ₹{r[2]:.2f}, Current: ₹{r[3]:.2f if r[3] else 0:.2f}, P&L: ₹{r[4]:.2f if r[4] else 0:.2f}') for r in cur.fetchall()]"
```

### **Check Pending Signals:**
```bash
py -c "import psycopg2; from config.settings import get_settings; s = get_settings(); conn = psycopg2.connect(host=s.DB_HOST, port=s.DB_PORT, database=s.DB_NAME, user=s.DB_USER, password=s.DB_PASSWORD); cur = conn.cursor(); cur.execute('SELECT symbol, signal_type, entry_price, confidence, status FROM signals WHERE status=''PENDING'' ORDER BY confidence DESC'); [print(f'{r[0]}: {r[1]} @ ₹{r[2]:.2f} ({r[3]}% conf)') for r in cur.fetchall()]"
```

### **Monitor API Logs:**
```bash
tail -f logs/api.log
```

### **Monitor Engine Logs:**
```bash
tail -f logs/paper_trading_engine.log
```

---

## 📊 Data Flow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW DIAGRAM                        │
└─────────────────────────────────────────────────────────────┘

[1] Signal Generation (Manual)
    generate_nifty50_signals.py
         ↓
    Zerodha API (Live Prices)
         ↓
    INSERT INTO signals (status=PENDING)

[2] Trading Engine Loop (Every 60s)
    paper_trading_engine.py
         ↓
    Get pending signals from DB
         ↓
    Zerodha API (Live Prices)
         ↓
    Execute BUY/SELL orders
         ↓
    UPDATE paper_positions
    UPDATE paper_portfolio
    UPDATE signals (status=ACTIVE)

[3] Price Update (Every 60s)
    paper_trading_engine.py
         ↓
    Zerodha API (Live Prices)
         ↓
    UPDATE paper_positions (current_price, pnl)

[4] API Layer (On Request)
    FastAPI Router
         ↓
    virtual_portfolio.get_positions()
         ↓
    SELECT * FROM paper_positions
         ↓
    Return JSON

[5] Frontend Display (Auto-refresh 30s)
    paper-trading.tsx
         ↓
    fetch('/api/paper-trading/positions')
         ↓
    Render table with live data
         ↓
    User sees updated P&L
```

---

## 🎯 Key Takeaways

1. **Database is Source of Truth**
   - All data stored in PostgreSQL
   - `paper_positions` table holds live prices
   - Updated every 60s by trading engine

2. **Two Update Cycles:**
   - **Backend:** 60s (engine updates DB)
   - **Frontend:** 30s (page fetches from API)
   - User sees data within 30-90s of price change

3. **Live Data Source:**
   - Zerodha Kite API
   - `kite.ltp()` for Last Traded Price
   - `kite.quote()` for full OHLCV data

4. **Automatic Trading:**
   - Signals auto-executed if price within 2% of entry
   - Positions auto-exited on stop-loss (-2%) or target (+3%)
   - Risk manager validates all trades

5. **NULL Handling:**
   - Database columns nullable for `current_price`, `pnl`
   - Frontend shows `-` when null
   - **Issue:** Some backend code still returns 0 instead of None

6. **Performance Optimizations:**
   - Cached portfolio instance (reused DB connection)
   - Parallel API calls in frontend
   - Batch price fetching from Zerodha

---

## 🔧 Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| [paper-trading.tsx](dashboard/pages/paper-trading.tsx) | Frontend UI | 350 |
| [paper_trading.py](services/api/routers/paper_trading.py) | API endpoints | 200 |
| [virtual_portfolio.py](services/paper_trading/virtual_portfolio.py) | Portfolio operations | 480 |
| [paper_trading_engine.py](services/paper_trading/paper_trading_engine.py) | Auto-trading engine | 365 |
| [generate_nifty50_signals.py](generate_nifty50_signals.py) | Signal generator | 130 |
| [zerodha_adapter.py](services/market_data/adapters/zerodha_adapter.py) | Market data API | 300 |
| [risk_manager.py](services/paper_trading/risk_manager.py) | Risk validation | 250 |

---

**End of Document**
