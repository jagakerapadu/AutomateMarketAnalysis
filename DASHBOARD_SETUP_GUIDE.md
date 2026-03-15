# 🎯 DASHBOARD SETUP CHECKLIST

**Issue:** Dashboard is empty  
**Root Cause:** Backend API server is NOT running  
**Status:** ✅ Database UP | ❌ Backend API DOWN | ✅ Dashboard Frontend UP

---

## Current Status

### ✅ What's Working:
- **Database**: TimescaleDB running on port 5434 ✓
- **Data**: Database has data (16 positions, 30 signals, 27 orders) ✓
- **Dashboard Frontend**: Running on port 3000 (npm run dev) ✓

### ❌ What's Missing:
- **Backend API Server**: NOT running on port 8000 ❌
  - The dashboard tries to fetch data from `http://localhost:8000`
  - No server is listening on that port
  - **This is why your dashboard is empty!**

---

## 📋 PREREQUISITES CHECKLIST

### Step 1: Start Backend API Server (REQUIRED)

**Option A: Run API Locally (Recommended)**
```powershell
# Open a new PowerShell terminal
cd C:\Share_Market\jagakerapadu\AutomateMarketAnalysis

# Start the API server
py start_api.py
```

This will start the FastAPI server on `http://localhost:8000`

**Option B: Run via Docker Compose (Full Stack)**
```powershell
# Stop current containers
docker-compose down

# Start all services (database + backend + dashboard)
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

### Step 2: Verify API is Running

**Check if API responds:**
```powershell
# Open browser or run:
curl http://localhost:8000/api/health

# Or check API docs:
# http://localhost:8000/api/docs
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-15T...",
  "database": "connected"
}
```

---

### Step 3: Verify API Endpoints Have Data

**Test key endpoints the dashboard needs:**

1. **Portfolio Summary:**
   ```
   http://localhost:8000/api/portfolio/summary
   ```

2. **Latest Signals:**
   ```
   http://localhost:8000/api/signals/latest?limit=10
   ```

3. **Market Overview:**
   ```
   http://localhost:8000/api/market/overview
   ```

4. **Trade Stats:**
   ```
   http://localhost:8000/api/trades/stats?days=30
   ```

---

### Step 4: Dashboard Configuration

**Verify environment variable:**
```powershell
# In dashboard directory, check .env.local file
cat dashboard\.env.local
```

**Should contain:**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If file doesn't exist, create it:
```powershell
cd dashboard
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

---

### Step 5: Restart Dashboard (if needed)

```powershell
# In dashboard directory
cd dashboard

# Stop current dev server (CTRL+C)
# Then restart:
npm run dev
```

---

## 🎯 QUICK START (Recommended Order)

### Terminal 1 - Backend API:
```powershell
cd C:\Share_Market\jagakerapadu\AutomateMarketAnalysis
py start_api.py
```

### Terminal 2 - Dashboard:
```powershell
cd C:\Share_Market\jagakerapadu\AutomateMarketAnalysis\dashboard
npm run dev
```

### Terminal 3 - (Optional) Check Services:
```powershell
# Check if API is running
curl http://localhost:8000/api/health

# Check database
docker ps

# View API logs if needed
# (Terminal 1 will show logs)
```

---

## 🔍 TROUBLESHOOTING

### Dashboard still empty after starting API?

**1. Check browser console (F12):**
- Look for CORS errors
- Look for network errors (failed API calls)
- Check if requests are going to `http://localhost:8000`

**2. Hard refresh dashboard:**
- Press `CTRL + SHIFT + R` (Windows/Linux)
- Or `CMD + SHIFT + R` (Mac)

**3. Check API is accessible:**
```powershell
# Test from PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/summary"
```

**4. Verify data exists in database:**
```powershell
py -c "from config.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT COUNT(*) FROM paper_positions')); print('Positions:', result.fetchone()[0])"
```

### CORS Errors?

The API should allow `http://localhost:3000`. If you see CORS errors, the API configuration is correct but API might not be running.

### Port Already in Use?

```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill process if needed (replace PID)
taskkill /PID <PID> /F
```

---

## ✅ SUCCESS CRITERIA

You'll know it's working when:

1. **Terminal 1**: API server shows:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     Application startup complete
   ```

2. **Browser** (`http://localhost:8000/api/docs`):
   - Shows interactive API documentation
   - Can test endpoints

3. **Dashboard** (`http://localhost:3000`):
   - Shows market data (NIFTY 50, Bank Nifty)
   - Shows portfolio summary (capital, P&L)
   - Shows recent signals
   - Shows trade statistics

---

## 📦 REQUIRED SERVICES SUMMARY

| Service | Port | Status | Start Command |
|---------|------|--------|---------------|
| **TimescaleDB** | 5434 | ✅ Running | `docker-compose up -d timescaledb` |
| **Backend API** | 8000 | ❌ **NOT RUNNING** | `py start_api.py` |
| **Dashboard** | 3000 | ✅ Running | `npm run dev` (in dashboard/) |

---

## 🚀 NEXT STEPS

1. **Open new PowerShell terminal**
2. **Run:** `py start_api.py`
3. **Wait for:** "Uvicorn running on http://0.0.0.0:8000"
4. **Refresh dashboard:** Press F5 in browser
5. **Dashboard should now show data!**

The backend API is the missing piece - start it and your dashboard will come to life! 🎉
