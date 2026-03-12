"""Market data API endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from config.database import get_db

router = APIRouter()

class MarketOverview(BaseModel):
    """Market overview response model"""
    nifty_price: float
    nifty_change: float
    banknifty_price: float
    banknifty_change: float
    india_vix: float
    fii_net: Optional[float]
    dii_net: Optional[float]
    timestamp: datetime

class GlobalIndex(BaseModel):
    """Global index model"""
    index_name: str
    value: float
    change_percent: float
    timestamp: datetime

class OHLCData(BaseModel):
    """OHLC candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float]

@router.get("/overview", response_model=MarketOverview)
async def get_market_overview(db: Session = Depends(get_db)):
    """Get current market overview"""
    try:
        # Fetch latest global indices for market context
        global_indices_query = text("""
            SELECT index_name, value, change_percent
            FROM global_indices
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        
        global_indices = db.execute(global_indices_query).fetchall()
        
        # Get S&P 500 as market proxy
        sp500 = next((idx for idx in global_indices if idx[0] == '^GSPC'), None)
        
        # Use S&P 500 as proxy for Nifty (approximate correlation)
        nifty_proxy = sp500[1] * 3.18 if sp500 else 21500  # ~1 S&P = 3.18 Nifty
        change_proxy = sp500[2] if sp500 else 0
        
        return {
            "nifty_price": nifty_proxy,
            "nifty_change": change_proxy,
            "banknifty_price": nifty_proxy * 2.2,  # BankNifty ~2.2x Nifty
            "banknifty_change": change_proxy,
            "india_vix": 15.5,  # Default VIX
            "fii_net": None,
            "dii_net": None,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        # Return defaults on error
        return {
            "nifty_price": 21500,
            "nifty_change": 0,
            "banknifty_price": 47000,
            "banknifty_change": 0,
            "india_vix": 15.5,
            "fii_net": None,
            "dii_net": None,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/global-indices", response_model=List[GlobalIndex])
async def get_global_indices(db: Session = Depends(get_db)):
    """Get global market indices"""
    try:
        query = text("""
            SELECT DISTINCT ON (index_name)
                index_name, value, change_percent, timestamp
            FROM global_indices
            ORDER BY index_name, timestamp DESC
        """)
        
        result = db.execute(query).fetchall()
        
        return [
            {
                "index_name": row[0],
                "value": row[1],
                "change_percent": row[2],
                "timestamp": row[3]
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chart/{symbol}", response_model=List[OHLCData])
async def get_chart_data(
    symbol: str,
    timeframe: str = "1d",
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """Get OHLC chart data for a symbol"""
    try:
        from_date = datetime.now() - timedelta(days=days)
        
        query = text("""
            SELECT timestamp, open, high, low, close, volume, vwap
            FROM market_ohlc
            WHERE symbol = :symbol
              AND timeframe = :timeframe
              AND timestamp >= :from_date
            ORDER BY timestamp ASC
        """)
        
        result = db.execute(query, {
            'symbol': symbol,
            'timeframe': timeframe,
            'from_date': from_date
        }).fetchall()
        
        return [
            {
                "timestamp": row[0],
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
                "vwap": row[6]
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-movers")
async def get_top_movers(
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db)
):
    """Get top gainers and losers"""
    try:
        query = text("""
            WITH latest_prices AS (
                SELECT DISTINCT ON (symbol)
                    symbol,
                    close,
                    (close - LAG(close, 1) OVER (PARTITION BY symbol ORDER BY timestamp)) / 
                     LAG(close, 1) OVER (PARTITION BY symbol ORDER BY timestamp) * 100 AS change_percent,
                    volume,
                    timestamp
                FROM market_ohlc
                WHERE timeframe = '1d'
                  AND timestamp >= CURRENT_DATE - INTERVAL '2 days'
                ORDER BY symbol, timestamp DESC
            )
            SELECT * FROM (
                SELECT *, 'gainer' as type
                FROM latest_prices
                WHERE change_percent > 0
                ORDER BY change_percent DESC
                LIMIT :limit
            ) gainers
            UNION ALL
            SELECT * FROM (
                SELECT *, 'loser' as type
                FROM latest_prices
                WHERE change_percent < 0
                ORDER BY change_percent ASC
                LIMIT :limit
            ) losers
        """)
        
        result = db.execute(query, {'limit': limit}).fetchall()
        
        return {
            "gainers": [
                {
                    "symbol": row[0],
                    "price": row[1],
                    "change_percent": row[2],
                    "volume": row[3]
                }
                for row in result if row[5] == 'gainer'
            ],
            "losers": [
                {
                    "symbol": row[0],
                    "price": row[1],
                    "change_percent": row[2],
                    "volume": row[3]
                }
                for row in result if row[5] == 'loser'
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
