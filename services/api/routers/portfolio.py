"""Portfolio API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
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

class CombinedPortfolioSummary(BaseModel):
    """Combined portfolio summary (stocks + options)"""
    total_capital: float
    invested: float
    available: float
    total_pnl: float
    open_positions: int
    stocks_pnl: float
    options_pnl: float

@router.get("/combined-summary", response_model=CombinedPortfolioSummary)
async def get_combined_portfolio_summary(db: Session = Depends(get_db)):
    """Get combined portfolio summary (stocks + options)"""
    try:
        # Get stock portfolio data
        stock_query = text("""
            SELECT 
                total_capital,
                available_cash,
                invested_amount,
                total_pnl
            FROM paper_portfolio
            WHERE id = 1
        """)
        
        stock_portfolio = db.execute(stock_query).fetchone()
        
        # Get options portfolio data
        options_query = text("""
            SELECT 
                total_capital,
                available_cash,
                invested_amount,
                total_pnl
            FROM paper_options_portfolio
            WHERE id = 1
        """)
        
        options_portfolio = db.execute(options_query).fetchone()
        
        # Get position counts
        stock_count = db.execute(text("SELECT COUNT(*) FROM paper_positions WHERE quantity > 0")).scalar() or 0
        options_count = db.execute(text("SELECT COUNT(*) FROM paper_options_positions WHERE quantity > 0")).scalar() or 0
        
        # Combine data
        if stock_portfolio and options_portfolio:
            combined_capital = float(stock_portfolio[0]) + float(options_portfolio[0])
            combined_available = float(stock_portfolio[1]) + float(options_portfolio[1])
            combined_invested = float(stock_portfolio[2]) + float(options_portfolio[2])
            stocks_pnl = float(stock_portfolio[3])
            options_pnl = float(options_portfolio[3])
            combined_pnl = stocks_pnl + options_pnl
            
            return {
                "total_capital": combined_capital,
                "invested": combined_invested,
                "available": combined_available,
                "total_pnl": combined_pnl,
                "open_positions": stock_count + options_count,
                "stocks_pnl": stocks_pnl,
                "options_pnl": options_pnl
            }
        else:
            return {
                "total_capital": 2000000.0,
                "invested": 0.0,
                "available": 2000000.0,
                "total_pnl": 0.0,
                "open_positions": 0,
                "stocks_pnl": 0.0,
                "options_pnl": 0.0
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get portfolio summary - Calculate P&L from positions"""
    try:
        # Get paper trading portfolio data
        portfolio_query = text("""
            SELECT 
                total_capital,
                available_cash,
                invested_amount,
                total_pnl
            FROM paper_portfolio
            WHERE id = 1
        """)
        
        portfolio = db.execute(portfolio_query).fetchone()
        
        # Get position count
        count_query = text("SELECT COUNT(*) FROM paper_positions WHERE quantity > 0")
        position_count = db.execute(count_query).scalar()
        
        if portfolio:
            return {
                "total_capital": float(portfolio[0]),
                "invested": float(portfolio[2]),  # invested_amount
                "available": float(portfolio[1]),  # available_cash
                "total_pnl": float(portfolio[3]),  # total_pnl from database
                "open_positions": position_count or 0
            }
        else:
            # Fallback if no portfolio exists
            return {
                "total_capital": 1000000.0,
                "invested": 0.0,
                "available": 1000000.0,
                "total_pnl": 0.0,
                "open_positions": 0
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions", response_model=List[Position])
async def get_open_positions(db: Session = Depends(get_db)):
    """Get all open positions - FIXED to use paper_positions table"""
    try:
        query = text("""
            SELECT 
                symbol,
                position_type as strategy,
                quantity,
                avg_price as entry_price,
                current_price,
                pnl as unrealized_pnl,
                pnl_percent
            FROM paper_positions
            WHERE quantity > 0
            ORDER BY pnl DESC
        """)
        
        result = db.execute(query).fetchall()
        
        return [
            {
                "symbol": row[0],
                "strategy": row[1] or "LONG",
                "quantity": row[2],
                "entry_price": float(row[3]),
                "current_price": float(row[4]) if row[4] else float(row[3]),
                "unrealized_pnl": float(row[5]) if row[5] else 0.0,
                "pnl_percent": float(row[6]) if row[6] else 0.0
            }
            for row in result
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
