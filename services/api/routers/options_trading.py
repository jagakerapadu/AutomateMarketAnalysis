"""
Options Paper Trading API Router - Endpoints for options trading
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.database import get_db
from services.paper_trading.options_virtual_portfolio import OptionsVirtualPortfolio
from pydantic import BaseModel


router = APIRouter(prefix="/api/options-trading", tags=["Options Trading"])

# Pydantic models
class OptionsPortfolioSummary(BaseModel):
    total_capital: float
    available_cash: float
    invested_amount: float
    total_pnl: float
    today_pnl: float
    total_premium_paid: float
    total_premium_received: float
    positions_count: int
    updated_at: datetime

class OptionsPosition(BaseModel):
    id: int
    symbol: str
    strike: float
    option_type: str  # CE or PE
    expiry_date: str
    quantity: int  # Lots
    entry_premium: float
    current_premium: Optional[float]
    invested_value: float
    current_value: Optional[float]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    position_type: str
    strategy: Optional[str]
    days_to_expiry: Optional[int]
    opened_at: datetime
    updated_at: datetime

class OptionsOrder(BaseModel):
    order_id: str
    symbol: str
    strike: float
    option_type: str
    expiry_date: str
    order_type: str  # BUY or SELL
    quantity: int
    executed_premium: Optional[float]
    total_cost: Optional[float]
    status: str
    strategy: Optional[str]
    confidence: Optional[float]
    placed_at: datetime
    executed_at: Optional[datetime]

class OptionsSignal(BaseModel):
    id: int
    timestamp: datetime
    symbol: str
    strike: float
    option_type: str
    expiry_date: str
    signal_type: str
    strategy: str
    entry_premium: float
    target_premium: Optional[float]
    stop_loss_premium: Optional[float]
    confidence: Optional[float]
    current_spot_price: Optional[float]
    pcr_ratio: Optional[float]
    status: str
    reason: Optional[str]

class OptionsStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_profit: float
    avg_loss: float
    largest_win: float
    largest_loss: float


# Endpoints
@router.get("/portfolio", response_model=OptionsPortfolioSummary)
async def get_options_portfolio(db: Session = Depends(get_db)):
    """Get options portfolio summary"""
    try:
        result = db.execute(text("""
            SELECT 
                total_capital,
                available_cash,
                invested_amount,
                total_pnl,
                today_pnl,
                total_premium_paid,
                total_premium_received,
                updated_at
            FROM paper_options_portfolio
            ORDER BY updated_at DESC
            LIMIT 1
        """))
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Options portfolio not found")
        
        # Count active positions
        positions_count = db.execute(text("""
            SELECT COUNT(*) FROM paper_options_positions
        """)).scalar()
        
        return OptionsPortfolioSummary(
            total_capital=float(row[0]),
            available_cash=float(row[1]),
            invested_amount=float(row[2]),
            total_pnl=float(row[3]),
            today_pnl=float(row[4]),
            total_premium_paid=float(row[5]),
            total_premium_received=float(row[6]),
            positions_count=positions_count,
            updated_at=row[7]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions", response_model=List[OptionsPosition])
async def get_options_positions(db: Session = Depends(get_db)):
    """Get all active options positions"""
    try:
        result = db.execute(text("""
            SELECT 
                id,
                symbol,
                strike,
                option_type,
                expiry_date,
                quantity,
                entry_premium,
                current_premium,
                invested_value,
                current_value,
                pnl,
                pnl_percent,
                position_type,
                strategy,
                days_to_expiry,
                opened_at,
                updated_at
            FROM paper_options_positions
            ORDER BY opened_at DESC
        """))
        
        positions = []
        for row in result:
            positions.append(OptionsPosition(
                id=row[0],
                symbol=row[1],
                strike=float(row[2]),
                option_type=row[3],
                expiry_date=row[4].isoformat() if row[4] else None,
                quantity=row[5],
                entry_premium=float(row[6]),
                current_premium=float(row[7]) if row[7] else None,
                invested_value=float(row[8]),
                current_value=float(row[9]) if row[9] else None,
                pnl=float(row[10]) if row[10] else None,
                pnl_percent=float(row[11]) if row[11] else None,
                position_type=row[12],
                strategy=row[13],
                days_to_expiry=row[14],
                opened_at=row[15],
                updated_at=row[16]
            ))
        
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=List[OptionsOrder])
async def get_options_orders(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
):
    """Get options order history"""
    try:
        result = db.execute(text("""
            SELECT 
                order_id,
                symbol,
                strike,
                option_type,
                expiry_date,
                order_type,
                quantity,
                executed_premium,
                total_cost,
                status,
                strategy,
                confidence,
                placed_at,
                executed_at
            FROM paper_options_orders
            ORDER BY placed_at DESC
            LIMIT :limit
        """), {"limit": limit})
        
        orders = []
        for row in result:
            orders.append(OptionsOrder(
                order_id=row[0],
                symbol=row[1],
                strike=float(row[2]),
                option_type=row[3],
                expiry_date=row[4].isoformat() if row[4] else None,
                order_type=row[5],
                quantity=row[6],
                executed_premium=float(row[7]) if row[7] else None,
                total_cost=float(row[8]) if row[8] else None,
                status=row[9],
                strategy=row[10],
                confidence=float(row[11]) if row[11] else None,
                placed_at=row[12],
                executed_at=row[13]
            ))
        
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals", response_model=List[OptionsSignal])
async def get_options_signals(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db)
):
    """Get options trading signals"""
    try:
        query = """
            SELECT 
                id,
                timestamp,
                symbol,
                strike,
                option_type,
                expiry_date,
                signal_type,
                strategy,
                entry_premium,
                target_premium,
                stop_loss_premium,
                confidence,
                current_spot_price,
                pcr_ratio,
                status,
                reason
            FROM options_signals
        """
        
        if status:
            query += " WHERE status = :status"
        
        query += " ORDER BY timestamp DESC LIMIT :limit"
        
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        result = db.execute(text(query), params)
        
        signals = []
        for row in result:
            signals.append(OptionsSignal(
                id=row[0],
                timestamp=row[1],
                symbol=row[2],
                strike=float(row[3]),
                option_type=row[4],
                expiry_date=row[5].isoformat() if row[5] else None,
                signal_type=row[6],
                strategy=row[7],
                entry_premium=float(row[8]),
                target_premium=float(row[9]) if row[9] else None,
                stop_loss_premium=float(row[10]) if row[10] else None,
                confidence=float(row[11]) if row[11] else None,
                current_spot_price=float(row[12]) if row[12] else None,
                pcr_ratio=float(row[13]) if row[13] else None,
                status=row[14],
                reason=row[15]
            ))
        
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=OptionsStats)
async def get_options_stats(db: Session = Depends(get_db)):
    """Get options trading statistics"""
    try:
        # Get closed trades stats
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(*) FILTER (WHERE pnl > 0) as winning_trades,
                COUNT(*) FILTER (WHERE pnl < 0) as losing_trades,
                COALESCE(SUM(pnl), 0) as total_pnl,
                COALESCE(AVG(pnl) FILTER (WHERE pnl > 0), 0) as avg_profit,
                COALESCE(AVG(pnl) FILTER (WHERE pnl < 0), 0) as avg_loss,
                COALESCE(MAX(pnl), 0) as largest_win,
                COALESCE(MIN(pnl), 0) as largest_loss
            FROM paper_options_orders
            WHERE status = 'EXECUTED' AND order_type = 'SELL'
        """))
        
        row = result.fetchone()
        
        total_trades = row[0] or 0
        winning_trades = row[1] or 0
        
        return OptionsStats(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=row[2] or 0,
            win_rate=round((winning_trades / total_trades * 100), 2) if total_trades > 0 else 0.0,
            total_pnl=float(row[3]),
            avg_profit=float(row[4]),
            avg_loss=float(row[5]),
            largest_win=float(row[6]),
            largest_loss=float(row[7])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def options_health_check():
    """Health check for options trading"""
    return {
        "status": "healthy",
        "service": "options_trading",
        "timestamp": datetime.now().isoformat()
    }
