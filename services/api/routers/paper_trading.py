"""
Paper Trading API Router - Endpoints for paper trading
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
from services.paper_trading.virtual_portfolio import VirtualPortfolio
from services.paper_trading.position_analyzer import PositionAnalyzer
from pydantic import BaseModel


router = APIRouter(prefix="/api/paper-trading", tags=["paper-trading"])

# Pydantic models
class PortfolioSummary(BaseModel):
    total_capital: float
    available_cash: float
    invested_amount: float
    total_pnl: float
    today_pnl: float
    positions_count: int
    updated_at: datetime

class Position(BaseModel):
    id: int
    symbol: str
    quantity: int
    avg_price: float
    current_price: Optional[float]
    invested_value: float
    current_value: Optional[float]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    position_type: str
    opened_at: datetime
    updated_at: datetime

class Order(BaseModel):
    order_id: str
    symbol: str
    order_type: str
    quantity: int
    price: Optional[float]
    executed_price: Optional[float]
    status: str
    placed_at: datetime
    executed_at: Optional[datetime]

class PlaceOrderRequest(BaseModel):
    symbol: str
    order_type: str  # BUY or SELL
    quantity: int
    price: float
    signal_id: Optional[int] = None


# Cached portfolio instance
_portfolio_instance = None

def get_portfolio():
    """Get or create portfolio instance"""
    global _portfolio_instance
    if _portfolio_instance is None:
        _portfolio_instance = VirtualPortfolio()
    return _portfolio_instance


@router.get("/portfolio", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """Get paper trading portfolio summary"""
    portfolio = get_portfolio()
    summary = portfolio.get_portfolio_summary()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return summary


@router.get("/positions", response_model=List[Position])
async def get_positions():
    """Get all current positions"""
    portfolio = get_portfolio()
    positions = portfolio.get_positions()
    return positions


@router.get("/orders", response_model=List[Order])
async def get_orders(limit: int = Query(default=50, le=200)):
    """Get order history"""
    portfolio = get_portfolio()
    orders = portfolio.get_orders(limit=limit)
    return orders


@router.post("/orders")
async def place_order(request: PlaceOrderRequest):
    """Place a paper trading order"""
    import time
    
    portfolio = get_portfolio()
    
    # Generate order ID
    order_id = f"PAPER_{request.symbol}_{int(time.time())}"
    
    # Place order
    success = portfolio.place_order(
        order_id=order_id,
        symbol=request.symbol,
        order_type=request.order_type,
        quantity=request.quantity,
        price=request.price,
        signal_id=request.signal_id
    )
    
    if success:
        return {
            "status": "success",
            "message": f"Order placed: {request.order_type} {request.quantity} {request.symbol}",
            "order_id": order_id
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to place order. Check funds and position.")


@router.post("/portfolio/reset")
async def reset_portfolio():
    """Reset portfolio to initial state"""
    portfolio = get_portfolio()
    portfolio.reset_portfolio()
    
    return {
        "status": "success",
        "message": "Portfolio reset to initial capital"
    }


@router.get("/stats")
async def get_trading_stats(days: int = Query(default=30, le=365)):
    """Get paper trading statistics"""
    from datetime import timezone
    
    portfolio = get_portfolio()
    
    # Get orders
    orders = portfolio.get_orders(limit=1000)
    
    # Filter by date - use timezone-aware datetime to match database
    from_date = datetime.now(timezone.utc) - timedelta(days=days)
    recent_orders = []
    for o in orders:
        exec_at = o.get('executed_at')
        if exec_at:
            # Database returns timezone-aware datetimes
            if isinstance(exec_at, datetime) and exec_at >= from_date:
                recent_orders.append(o)
    
    # Calculate stats
    buy_orders = [o for o in recent_orders if o['order_type'] == 'BUY']
    sell_orders = [o for o in recent_orders if o['order_type'] == 'SELL']
    
    summary = portfolio.get_portfolio_summary()
    
    return {
        'total_orders': len(recent_orders),
        'buy_orders': len(buy_orders),
        'sell_orders': len(sell_orders),
        'total_pnl': summary['total_pnl'] if summary else 0,
        'today_pnl': summary['today_pnl'] if summary else 0,
        'active_positions': summary['positions_count'] if summary else 0,
        'capital_deployed': summary['invested_amount'] if summary else 0,
        'available_cash': summary['available_cash'] if summary else 0    }


@router.get("/analysis/positions")
async def analyze_all_positions():
    """Analyze all open positions to identify what is going wrong"""
    analyzer = PositionAnalyzer()
    analysis = analyzer.analyze_all_positions()
    return analysis


@router.get("/analysis/position/{position_id}")
async def analyze_single_position(position_id: int):
    """Analyze a specific position"""
    analyzer = PositionAnalyzer()
    analysis = analyzer.analyze_position(position_id)
    
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    
    return analysis