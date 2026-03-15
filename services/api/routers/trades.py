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
    """Get combined trading statistics from current positions (stocks + options)"""
    try:
        # Get stats from current positions (stocks)
        stock_query = text("""
            SELECT 
                COUNT(*) as total_positions,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_positions,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_positions,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
                SUM(pnl) as total_pnl
            FROM paper_positions
            WHERE quantity > 0
        """)
        
        # Get stats from options positions
        options_query = text("""
            SELECT 
                COUNT(*) as total_positions,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_positions,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_positions,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
                SUM(pnl) as total_pnl
            FROM paper_options_positions
            WHERE quantity > 0
        """)
        
        stock_result = db.execute(stock_query).fetchone()
        options_result = db.execute(options_query).fetchone()
        
        # Count executed orders
        order_count_query = text("""
            SELECT 
                (SELECT COUNT(*) FROM paper_orders WHERE status = 'EXECUTED') +
                (SELECT COUNT(*) FROM paper_options_orders WHERE status = 'EXECUTED')
        """)
        total_orders = db.execute(order_count_query).scalar() or 0
        
        # Combine results
        total_positions = (stock_result[0] or 0) + (options_result[0] or 0)
        winning = (stock_result[1] or 0) + (options_result[1] or 0)
        losing = (stock_result[2] or 0) + (options_result[2] or 0)
        
        # Calculate weighted average wins/losses
        stock_wins = stock_result[1] or 0
        options_wins = options_result[1] or 0
        total_wins = stock_wins + options_wins
        
        if total_wins > 0:
            avg_win = ((stock_result[3] or 0) * stock_wins + (options_result[3] or 0) * options_wins) / total_wins
        else:
            avg_win = 0
            
        stock_losses = stock_result[2] or 0
        options_losses = options_result[2] or 0
        total_losses = stock_losses + options_losses
        
        if total_losses > 0:
            avg_loss = ((stock_result[4] or 0) * stock_losses + (options_result[4] or 0) * options_losses) / total_losses
        else:
            avg_loss = 0
        
        win_rate = (winning / total_positions * 100) if total_positions > 0 else 0
        
        total_pnl = (stock_result[5] or 0) + (options_result[5] or 0)
        
        return {
            "total_trades": total_orders,
            "closed_trades": 0,
            "open_trades": total_positions,
            "winning_trades": winning,
            "losing_trades": losing,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(float(total_pnl), 2),
            "avg_win": round(float(avg_win), 2) if avg_win else 0,
            "avg_loss": round(float(avg_loss), 2) if avg_loss else 0,
            "best_trade": round(float(max(stock_result[3] or 0, options_result[3] or 0)), 2),
            "worst_trade": round(float(min(stock_result[4] or 0, options_result[4] or 0)), 2)
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
