"""Backtest API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

from config.database import get_db

router = APIRouter()

class BacktestSummary(BaseModel):
    """Backtest summary model"""
    id: int
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    created_at: datetime

class BacktestDetail(BaseModel):
    """Detailed backtest result"""
    id: int
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    equity_curve: List[float]
    trades: List[dict]

@router.get("/results", response_model=List[BacktestSummary])
async def get_backtest_results(
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
):
    """Get backtest results summary"""
    try:
        conditions = []
        params = {'limit': limit}
        
        if strategy:
            conditions.append("strategy_name = :strategy")
            params['strategy'] = strategy
        
        if symbol:
            conditions.append("symbol = :symbol")
            params['symbol'] = symbol
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = text(f"""
            SELECT id, strategy_name, symbol, timeframe, start_date, end_date,
                   total_return_percent, sharpe_ratio, max_drawdown, win_rate,
                   total_trades, created_at
            FROM backtest_results
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, params).fetchall()
        
        return [
            {
                "id": row[0],
                "strategy_name": row[1],
                "symbol": row[2],
                "timeframe": row[3],
                "start_date": row[4],
                "end_date": row[5],
                "total_return_percent": row[6],
                "sharpe_ratio": row[7],
                "max_drawdown": row[8],
                "win_rate": row[9],
                "total_trades": row[10],
                "created_at": row[11]
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{backtest_id}", response_model=BacktestDetail)
async def get_backtest_detail(backtest_id: int, db: Session = Depends(get_db)):
    """Get detailed backtest result"""
    try:
        query = text("""
            SELECT *
            FROM backtest_results
            WHERE id = :id
        """)
        
        result = db.execute(query, {'id': backtest_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        return {
            "id": result[0],
            "strategy_name": result[1],
            "symbol": result[2],
            "timeframe": result[3],
            "start_date": result[4],
            "end_date": result[5],
            "initial_capital": result[6],
            "final_capital": result[7],
            "total_return": result[8],
            "total_return_percent": result[9],
            "sharpe_ratio": result[10],
            "max_drawdown": result[11],
            "win_rate": result[12],
            "total_trades": result[13],
            "winning_trades": result[14],
            "losing_trades": result[15],
            "avg_win": result[16],
            "avg_loss": result[17],
            "profit_factor": result[18],
            "equity_curve": json.loads(result[20]) if result[20] else [],
            "trades": json.loads(result[21]) if result[21] else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare")
async def compare_strategies(
    strategies: str = Query(..., description="Comma-separated strategy names"),
    symbol: str = "NIFTY 50",
    db: Session = Depends(get_db)
):
    """Compare multiple strategies"""
    try:
        strategy_list = [s.strip() for s in strategies.split(',')]
        
        query = text("""
            SELECT strategy_name, AVG(total_return_percent) as avg_return,
                   AVG(sharpe_ratio) as avg_sharpe,
                   AVG(win_rate) as avg_win_rate,
                   AVG(max_drawdown) as avg_drawdown
            FROM backtest_results
            WHERE strategy_name = ANY(:strategies)
              AND symbol = :symbol
            GROUP BY strategy_name
        """)
        
        result = db.execute(query, {
            'strategies': strategy_list,
            'symbol': symbol
        }).fetchall()
        
        return [
            {
                "strategy": row[0],
                "avg_return": round(row[1], 2) if row[1] else 0,
                "avg_sharpe": round(row[2], 2) if row[2] else 0,
                "avg_win_rate": round(row[3], 2) if row[3] else 0,
                "avg_drawdown": round(row[4], 2) if row[4] else 0
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
