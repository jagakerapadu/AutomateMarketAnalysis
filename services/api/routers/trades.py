"""Trades API endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from config.database import get_db

router = APIRouter()

class Trade(BaseModel):
    """Trade model"""
    id: int
    trade_id: str
    symbol: str
    strategy: str
    order_type: str
    quantity: int
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float]
    exit_time: Optional[datetime]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    status: str

@router.get("/", response_model=List[Trade])
async def get_trades(
    status: Optional[str] = None,
    days: int = Query(default=30, le=365),
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db)
):
    """Get trade history"""
    try:
        from_date = datetime.now() - timedelta(days=days)
        
        conditions = ["entry_time >= :from_date"]
        params = {'from_date': from_date, 'limit': limit}
        
        if status:
            conditions.append("status = :status")
            params['status'] = status
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT id, trade_id, symbol, strategy, order_type, quantity,
                   entry_price, entry_time, exit_price, exit_time,
                   pnl, pnl_percent, status
            FROM trades
            WHERE {where_clause}
            ORDER BY entry_time DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, params).fetchall()
        
        return [
            {
                "id": row[0],
                "trade_id": row[1],
                "symbol": row[2],
                "strategy": row[3],
                "order_type": row[4],
                "quantity": row[5],
                "entry_price": row[6],
                "entry_time": row[7],
                "exit_price": row[8],
                "exit_time": row[9],
                "pnl": row[10],
                "pnl_percent": row[11],
                "status": row[12]
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_trade_stats(
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """Get trading statistics"""
    try:
        from_date = datetime.now() - timedelta(days=days)
        
        query = text("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_trades,
                COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
                MAX(pnl) as best_trade,
                MIN(pnl) as worst_trade
            FROM trades
            WHERE entry_time >= :from_date
        """)
        
        result = db.execute(query, {'from_date': from_date}).fetchone()
        
        total_closed = result[1] or 0
        winning = result[3] or 0
        win_rate = (winning / total_closed * 100) if total_closed > 0 else 0
        
        return {
            "total_trades": result[0],
            "closed_trades": result[1],
            "open_trades": result[2],
            "winning_trades": winning,
            "losing_trades": result[4],
            "win_rate": round(win_rate, 2),
            "total_pnl": round(result[5], 2) if result[5] else 0,
            "avg_win": round(result[6], 2) if result[6] else 0,
            "avg_loss": round(result[7], 2) if result[7] else 0,
            "best_trade": round(result[8], 2) if result[8] else 0,
            "worst_trade": round(result[9], 2) if result[9] else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-pnl")
async def get_daily_pnl(
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """Get daily P&L"""
    try:
        from_date = datetime.now() - timedelta(days=days)
        
        query = text("""
            SELECT 
                DATE(entry_time) as trade_date,
                SUM(pnl) as daily_pnl,
                COUNT(*) as trades_count
            FROM trades
            WHERE entry_time >= :from_date
              AND status = 'CLOSED'
            GROUP BY DATE(entry_time)
            ORDER BY trade_date DESC
        """)
        
        result = db.execute(query, {'from_date': from_date}).fetchall()
        
        return [
            {
                "date": row[0].isoformat(),
                "pnl": round(row[1], 2) if row[1] else 0,
                "trades": row[2]
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
