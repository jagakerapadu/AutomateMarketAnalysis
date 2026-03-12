"""Backtest Engine - Historical strategy simulation"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import vectorbt as vbt
from dataclasses import dataclass, asdict
from sqlalchemy import text
from config.database import get_db_context
from config.logger import setup_logger
from services.strategy.base_strategy import BaseStrategy

logger = setup_logger("backtest_engine")

@dataclass
class BacktestResult:
    """Backtest result data structure"""
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
    trades: List[Dict]

class BacktestEngine:
    """Backtest trading strategies on historical data"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.commission = 0.001  # 0.1% per trade
    
    def run_backtest(
        self,
        strategy: BaseStrategy,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        Run backtest for a strategy
        
        Args:
            strategy: Strategy instance
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
        
        Returns:
            BacktestResult
        """
        logger.info(f"Running backtest for {strategy.name} on {symbol}")
        
        # Fetch historical data
        data = self._fetch_historical_data(
            symbol,
            strategy.timeframe,
            start_date,
            end_date
        )
        
        if data.empty or len(data) < 100:
            logger.error("Insufficient historical data for backtest")
            return self._empty_result(strategy, symbol, start_date, end_date)
        
        # Simulate trading
        trades, equity_curve = self._simulate_trading(strategy, data)
        
        # Calculate metrics
        result = self._calculate_metrics(
            strategy,
            symbol,
            data,
            trades,
            equity_curve,
            start_date,
            end_date
        )
        
        # Save to database
        self._save_backtest_result(result)
        
        logger.info(f"Backtest complete - Total Return: {result.total_return_percent:.2f}%, "
                   f"Win Rate: {result.win_rate:.2f}%")
        
        return result
    
    def _fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch historical OHLC data with indicators"""
        try:
            with get_db_context() as db:
                query = text("""
                    SELECT 
                        o.timestamp,
                        o.symbol,
                        o.open,
                        o.high,
                        o.low,
                        o.close,
                        o.volume,
                        o.vwap,
                        i.rsi,
                        i.macd,
                        i.macd_signal,
                        i.ema_9,
                        i.ema_21,
                        i.ema_50,
                        i.ema_200,
                        i.atr,
                        i.bb_upper,
                        i.bb_lower
                    FROM market_ohlc o
                    LEFT JOIN indicators i ON 
                        o.timestamp = i.timestamp AND 
                        o.symbol = i.symbol AND 
                        o.timeframe = i.timeframe
                    WHERE o.symbol = :symbol 
                      AND o.timeframe = :timeframe
                      AND o.timestamp >= :start_date
                      AND o.timestamp <= :end_date
                    ORDER BY o.timestamp ASC
                """)
                
                result = db.execute(query, {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'start_date': start_date,
                    'end_date': end_date
                })
                
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                return df
                
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def _simulate_trading(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame
    ) -> Tuple[List[Dict], List[float]]:
        """Simulate trading on historical data"""
        trades = []
        equity_curve = [self.initial_capital]
        capital = self.initial_capital
        position = None
        
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            
            if len(current_data) < strategy.min_data_points:
                continue
            
            row = current_data.iloc[-1]
            
            # No position - look for entry
            if position is None:
                signal = strategy.generate_signal(current_data)
                
                if signal and signal.quantity > 0:
                    # Enter position
                    entry_cost = signal.entry_price * signal.quantity
                    commission_cost = entry_cost * self.commission
                    
                    if capital >= (entry_cost + commission_cost):
                        position = {
                            'entry_time': row['timestamp'],
                            'entry_price': signal.entry_price,
                            'quantity': signal.quantity,
                            'stop_loss': signal.stop_loss,
                            'target': signal.target_price,
                            'signal_type': signal.signal_type.value
                        }
                        capital -= (entry_cost + commission_cost)
            
            # Has position - check exit conditions
            elif position is not None:
                current_price = row['close']
                
                # Hit stop loss
                if current_price <= position['stop_loss']:
                    exit_price = position['stop_loss']
                    pnl = self._calculate_pnl(position, exit_price)
                    capital += pnl
                    
                    trades.append({
                        **position,
                        'exit_time': row['timestamp'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_percent': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                        'exit_reason': 'Stop Loss'
                    })
                    position = None
                
                # Hit target
                elif current_price >= position['target']:
                    exit_price = position['target']
                    pnl = self._calculate_pnl(position, exit_price)
                    capital += pnl
                    
                    trades.append({
                        **position,
                        'exit_time': row['timestamp'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_percent': (pnl / (position['entry_price'] * position['quantity'])) * 100,
                        'exit_reason': 'Target Hit'
                    })
                    position = None
            
            # Update equity curve
            current_equity = capital
            if position is not None:
                current_equity += row['close'] * position['quantity']
            
            equity_curve.append(current_equity)
        
        return trades, equity_curve
    
    def _calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """Calculate P&L for a position"""
        entry_value = position['entry_price'] * position['quantity']
        exit_value = exit_price * position['quantity']
        
        gross_pnl = exit_value - entry_value
        commission = (entry_value + exit_value) * self.commission
        
        return gross_pnl - commission
    
    def _calculate_metrics(
        self,
        strategy: BaseStrategy,
        symbol: str,
        data: pd.DataFrame,
        trades: List[Dict],
        equity_curve: List[float],
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Calculate backtest performance metrics"""
        
        # Basic metrics
        final_capital = equity_curve[-1]
        total_return = final_capital - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100
        
        # Trade statistics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Average win/loss
        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] < 0]
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        # Sharpe ratio
        returns = pd.Series(equity_curve).pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 0 else 0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = abs(drawdown.min()) * 100
        
        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            timeframe=strategy.timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_percent=total_return_percent,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            equity_curve=equity_curve,
            trades=trades
        )
    
    def _empty_result(self, strategy, symbol, start_date, end_date) -> BacktestResult:
        """Return empty result for failed backtest"""
        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            timeframe=strategy.timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return=0,
            total_return_percent=0,
            sharpe_ratio=0,
            max_drawdown=0,
            win_rate=0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            avg_win=0,
            avg_loss=0,
            profit_factor=0,
            equity_curve=[self.initial_capital],
            trades=[]
        )
    
    def _save_backtest_result(self, result: BacktestResult) -> bool:
        """Save backtest result to database"""
        try:
            with get_db_context() as db:
                insert_query = text("""
                    INSERT INTO backtest_results (
                        strategy_name, symbol, timeframe, start_date, end_date,
                        initial_capital, final_capital, total_return, total_return_percent,
                        sharpe_ratio, max_drawdown, win_rate, total_trades,
                        winning_trades, losing_trades, avg_win, avg_loss, profit_factor,
                        equity_curve, trades
                    ) VALUES (
                        :strategy_name, :symbol, :timeframe, :start_date, :end_date,
                        :initial_capital, :final_capital, :total_return, :total_return_percent,
                        :sharpe_ratio, :max_drawdown, :win_rate, :total_trades,
                        :winning_trades, :losing_trades, :avg_win, :avg_loss, :profit_factor,
                        :equity_curve, :trades
                    )
                """)
                
                result_dict = asdict(result)
                # Convert lists to JSON for JSONB columns
                import json
                result_dict['equity_curve'] = json.dumps(result.equity_curve)
                result_dict['trades'] = json.dumps(result.trades)
                
                db.execute(insert_query, result_dict)
                logger.info("Backtest result saved to database")
                return True
                
        except Exception as e:
            logger.error(f"Error saving backtest result: {e}")
            return False
