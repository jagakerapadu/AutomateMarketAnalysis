"""Portfolio API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from config.database import get_db

router = APIRouter()

class Position(BaseModel):
    """Open position model"""
    symbol: str
    strategy: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    pnl_percent: float

class PortfolioSummary(BaseModel):
    """Portfolio summary"""
    total_capital: float
    invested: float
    available: float
    total_pnl: float
    open_positions: int

@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get portfolio summary"""
    try:
        # Get open positions value
        positions_query = text("""
            SELECT 
                COUNT(*) as open_positions,
                SUM(quantity * entry_price) as invested_value
            FROM trades
            WHERE status = 'OPEN'
        """)
        
        positions = db.execute(positions_query).fetchone()
        
        # Get total P&L
        pnl_query = text("""
            SELECT SUM(pnl) as total_pnl
            FROM trades
            WHERE status = 'CLOSED'
        """)
        
        pnl_result = db.execute(pnl_query).fetchone()
        
        total_capital = 100000  # Default starting capital
        invested = positions[1] if positions and positions[1] else 0
        total_pnl = pnl_result[0] if pnl_result and pnl_result[0] else 0
        
        return {
            "total_capital": total_capital + total_pnl,
            "invested": invested,
            "available": total_capital + total_pnl - invested,
            "total_pnl": total_pnl,
            "open_positions": positions[0] if positions else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions", response_model=List[Position])
async def get_open_positions(db: Session = Depends(get_db)):
    """Get all open positions"""
    try:
        query = text("""
            SELECT 
                t.symbol,
                t.strategy,
                t.quantity,
                t.entry_price,
                o.close as current_price,
                (o.close * t.quantity - t.entry_price * t.quantity) as unrealized_pnl,
                ((o.close - t.entry_price) / t.entry_price * 100) as pnl_percent
            FROM trades t
            JOIN LATERAL (
                SELECT close
                FROM market_ohlc
                WHERE symbol = t.symbol
                  AND timeframe = '1d'
                ORDER BY timestamp DESC
                LIMIT 1
            ) o ON true
            WHERE t.status = 'OPEN'
        """)
        
        result = db.execute(query).fetchall()
        
        return [
            {
                "symbol": row[0],
                "strategy": row[1],
                "quantity": row[2],
                "entry_price": row[3],
                "current_price": row[4],
                "unrealized_pnl": round(row[5], 2) if row[5] else 0,
                "pnl_percent": round(row[6], 2) if row[6] else 0
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
