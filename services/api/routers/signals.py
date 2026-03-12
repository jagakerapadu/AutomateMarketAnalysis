"""Trading signals API endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from config.database import get_db

router = APIRouter()

class Signal(BaseModel):
    """Trading signal model"""
    id: int
    timestamp: datetime
    symbol: str
    strategy: str
    signal_type: str
    timeframe: str
    entry_price: float
    stop_loss: float
    target_price: float
    confidence: float
    quantity: Optional[int]
    reason: str
    status: str

@router.get("/latest", response_model=List[Signal])
async def get_latest_signals(
    limit: int = Query(default=20, le=100),
    min_confidence: float = Query(default=60.0, ge=0, le=100),
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """Get latest trading signals"""
    try:
        from datetime import datetime, timedelta
        from_date = datetime.now() - timedelta(days=days)
        
        query = text("""
            SELECT id, timestamp, symbol, strategy, signal_type, timeframe,
                   entry_price, stop_loss, target_price, confidence, quantity,
                   reason, status
            FROM signals
            WHERE confidence >= :min_confidence
              AND timestamp >= :from_date
            ORDER BY confidence DESC, timestamp DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {
            'min_confidence': min_confidence,
            'from_date': from_date,
            'limit': limit
        }).fetchall()
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "symbol": row[2],
                "strategy": row[3],
                "signal_type": row[4],
                "timeframe": row[5],
                "entry_price": row[6],
                "stop_loss": row[7],
                "target_price": row[8],
                "confidence": row[9],
                "quantity": row[10],
                "reason": row[11],
                "status": row[12]
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-strategy/{strategy_name}")
async def get_signals_by_strategy(
    strategy_name: str,
    days: int = Query(default=7, le=90),
    db: Session = Depends(get_db)
):
    """Get signals for a specific strategy"""
    try:
        from_date = datetime.now() - timedelta(days=days)
        
        query = text("""
            SELECT id, timestamp, symbol, signal_type, entry_price,
                   stop_loss, target_price, confidence, status
            FROM signals
            WHERE strategy = :strategy
              AND timestamp >= :from_date
            ORDER BY timestamp DESC
        """)
        
        result = db.execute(query, {
            'strategy': strategy_name,
            'from_date': from_date
        }).fetchall()
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "symbol": row[2],
                "signal_type": row[3],
                "entry_price": row[4],
                "stop_loss": row[5],
                "target_price": row[6],
                "confidence": row[7],
                "status": row[8]
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_signal_stats(
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """Get signal statistics"""
    try:
        from_date = datetime.now() - timedelta(days=days)
        
        query = text("""
            SELECT 
                COUNT(*) as total_signals,
                COUNT(CASE WHEN status = 'EXECUTED' THEN 1 END) as executed,
                COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
                AVG(confidence) as avg_confidence,
                COUNT(DISTINCT strategy) as total_strategies,
                COUNT(DISTINCT symbol) as total_symbols
            FROM signals
            WHERE timestamp >= :from_date
        """)
        
        result = db.execute(query, {'from_date': from_date}).fetchone()
        
        return {
            "total_signals": result[0],
            "executed": result[1],
            "pending": result[2],
            "avg_confidence": round(result[3], 2) if result[3] else 0,
            "total_strategies": result[4],
            "total_symbols": result[5]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
