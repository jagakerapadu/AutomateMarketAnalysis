"""
Options Trading Analytics - End-of-Day Analysis
Analyzes what went well and what went wrong
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone, timedelta, date
from typing import Dict, List
import psycopg2
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("options_analytics")
settings = get_settings()


class OptionsAnalytics:
    """End-of-day options trading analytics"""
    
    def __init__(self):
        self.conn = self._get_db_connection()
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
    
    def get_today_trades(self, trade_date: date = None) -> List[Dict]:
        """Get all trades executed today"""
        if trade_date is None:
            trade_date = date.today()
        
        cursor = self.conn.cursor()
        
        # Get all buy and sell orders for the day
        cursor.execute("""
            WITH entries AS (
                SELECT 
                    order_id, symbol, strike, option_type, expiry_date,
                    order_type, quantity, executed_premium, strategy,
                    executed_at, reason
                FROM paper_options_orders
                WHERE DATE(executed_at) = %s
                    AND order_type = 'BUY'
            ),
            exits AS (
                SELECT
                    symbol, strike, option_type, expiry_date,
                    executed_premium as exit_premium,
                    executed_at as exit_time,
                    exit_reason
                FROM paper_options_orders
                WHERE DATE(executed_at) = %s
                    AND order_type = 'SELL'
            )
            SELECT 
                e.order_id, e.symbol, e.strike, e.option_type, e.expiry_date,
                e.quantity, e.executed_premium, e.strategy, e.executed_at, e.reason,
                x.exit_premium, x.exit_time, x.exit_reason
            FROM entries e
            LEFT JOIN exits x ON 
                e.symbol = x.symbol AND 
                e.strike = x.strike AND 
                e.option_type = x.option_type AND
                e.expiry_date = x.expiry_date
            ORDER BY e.executed_at DESC
        """, (trade_date, trade_date))
        
        rows = cursor.fetchall()
        cursor.close()
        
        trades = []
        for row in rows:
            entry_premium = float(row[6])
            exit_premium = float(row[10]) if row[10] else None
            quantity = row[5]
            
            if exit_premium:
                pnl = (exit_premium - entry_premium) * quantity * 50  # Nifty lot size
                pnl_percent = ((exit_premium - entry_premium) / entry_premium) * 100
                hold_minutes = (row[11] - row[8]).total_seconds() / 60 if row[11] else 0
            else:
                pnl = 0
                pnl_percent = 0
                hold_minutes = 0
            
            trades.append({
                'order_id': row[0],
                'symbol': row[1],
                'strike': float(row[2]),
                'option_type': row[3],
                'expiry_date': row[4],
                'quantity': quantity,
                'entry_premium': entry_premium,
                'strategy': row[7],
                'entry_time': row[8],
                'entry_reason': row[9],
                'exit_premium': exit_premium,
                'exit_time': row[11],
                'exit_reason': row[12],
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'hold_duration_minutes': int(hold_minutes),
                'status': 'CLOSED' if exit_premium else 'OPEN'
            })
        
        return trades
    
    def analyze_trade(self, trade: Dict) -> Dict:
        """Analyze individual trade - what went well/wrong"""
        analysis = {
            'what_went_well': [],
            'what_went_wrong': [],
            'lessons_learned': [],
            'rating': 3  # 1-5 stars
        }
        
        if trade['status'] == 'OPEN':
            analysis['what_went_wrong'].append("Position still open - no conclusion yet")
            return analysis
        
        pnl_percent = trade['pnl_percent']
        exit_reason = trade['exit_reason']
        hold_duration = trade['hold_duration_minutes']
        
        # Analyze outcome
        if pnl_percent >= 60:
            analysis['what_went_well'].append(f"Excellent profit: +{pnl_percent:.1f}% achieved")
            analysis['what_went_well'].append(f"Target hit as per strategy")
            analysis['rating'] = 5
        elif pnl_percent >= 30:
            analysis['what_went_well'].append(f"Good profit: +{pnl_percent:.1f}%")
            analysis['rating'] = 4
        elif pnl_percent > 0:
            analysis['what_went_well'].append(f"Profitable trade: +{pnl_percent:.1f}%")
            analysis['rating'] = 3
        elif pnl_percent >= -20:
            analysis['what_went_wrong'].append(f"Small loss: {pnl_percent:.1f}%")
            analysis['what_went_wrong'].append("Stop loss protected capital")
            analysis['rating'] = 2
        else:
            analysis['what_went_wrong'].append(f"Significant loss: {pnl_percent:.1f}%")
            analysis['what_went_wrong'].append("Stop loss should have been tighter")
            analysis['rating'] = 1
        
        # Analyze exit reason
        if exit_reason == 'TARGET':
            analysis['what_went_well'].append("Exited at target - disciplined exit")
            analysis['lessons_learned'].append("Target-based exits work well")
        elif exit_reason == 'STOP_LOSS':
            analysis['what_went_wrong'].append("Stop loss hit - trade went against us")
            analysis['lessons_learned'].append("Review entry conditions - signal may have been weak")
        elif exit_reason == 'TIME_DECAY':
            analysis['what_went_wrong'].append("Time decay exit - theta erosion")
            analysis['lessons_learned'].append("Options lose value over time - exit earlier")
        elif exit_reason == 'EXPIRY':
            analysis['what_went_wrong'].append("Forced exit near expiry")
            analysis['lessons_learned'].append("Avoid holding till last day")
        
        # Analyze hold duration
        if hold_duration < 30:
            analysis['lessons_learned'].append(f"Very quick trade ({hold_duration} min) - might be overtrading")
        elif hold_duration > 300:  # 5 hours
            analysis['lessons_learned'].append(f"Long hold ({hold_duration // 60} hrs) - consider intraday exits")
        
        # Strategy-specific analysis
        strategy = trade['strategy']
        if strategy == 'ORB_Options':
            if pnl_percent > 0:
                analysis['what_went_well'].append("ORB strategy worked - breakout confirmed")
            else:
                analysis['what_went_wrong'].append("False breakout - ORB failed")
                analysis['lessons_learned'].append("Need stronger volume confirmation for ORB")
        
        elif strategy == 'IV_Spike':
            if pnl_percent > 0:
                analysis['what_went_well'].append("IV spike play successful")
            else:
                analysis['what_went_wrong'].append("IV dropped unexpectedly")
                analysis['lessons_learned'].append("IV can collapse quickly - tighter stops needed")
        
        return analysis
    
    def generate_eod_report(self, trade_date: date = None) -> Dict:
        """Generate comprehensive end-of-day report"""
        if trade_date is None:
            trade_date = date.today()
        
        trades = self.get_today_trades(trade_date)
        
        if not trades:
            logger.info(f"No trades on {trade_date}")
            return {}
        
        # Calculate metrics
        total_trades = len([t for t in trades if t['status'] == 'CLOSED'])
        winning_trades = len([t for t in trades if t['status'] == 'CLOSED' and t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['status'] == 'CLOSED' and t['pnl'] < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum([t['pnl'] for t in trades if t['status'] == 'CLOSED'])
        avg_win = sum([t['pnl'] for t in trades if t['status'] == 'CLOSED' and t['pnl'] > 0]) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum([t['pnl'] for t in trades if t['status'] == 'CLOSED' and t['pnl'] < 0]) / losing_trades if losing_trades > 0 else 0
        
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
        
        # Analyze each trade
        wins_analysis = []
        losses_analysis = []
        key_learnings = []
        
        for trade in trades:
            if trade['status'] == 'CLOSED':
                analysis = self.analyze_trade(trade)
                
                trade_summary = f"{trade['option_type']} {trade['strike']} @ ₹{trade['entry_premium']:.2f} → ₹{trade['exit_premium']:.2f} ({trade['pnl_percent']:.1f}%)"
                
                if trade['pnl'] > 0:
                    wins_analysis.append(f"✅ {trade_summary}: {', '.join(analysis['what_went_well'])}")
                else:
                    losses_analysis.append(f"❌ {trade_summary}: {', '.join(analysis['what_went_wrong'])}")
                
                key_learnings.extend(analysis['lessons_learned'])
        
        # Get portfolio data
        cursor = self.conn.cursor()
        cursor.execute("SELECT total_capital, total_pnl FROM paper_options_portfolio ORDER BY id DESC LIMIT 1")
        portfolio_row = cursor.fetchone()
        
        cursor.execute("SELECT nifty_spot, india_vix FROM options_market_indicators ORDER BY timestamp DESC LIMIT 1")
        market_row = cursor.fetchone()
        
        cursor.close()
        
        report = {
            'trade_date': trade_date,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_profit': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'wins_analysis': wins_analysis,
            'losses_analysis': losses_analysis,
            'key_learnings': list(set(key_learnings)),  # Remove duplicates
            'ending_capital': float(portfolio_row[0]) if portfolio_row else 0,
            'total_portfolio_pnl': float(portfolio_row[1]) if portfolio_row else 0,
            'nifty_close': float(market_row[0]) if market_row else 0,
            'vix': float(market_row[1]) if market_row else 0
        }
        
        return report
    
    def print_eod_report(self, report: Dict):
        """Print formatted end-of-day report"""
        if not report:
            print("No report available")
            return
        
        print("\n" + "=" * 80)
        print(f"OPTIONS TRADING - END OF DAY REPORT")
        print(f"Date: {report['trade_date']}")
        print("=" * 80)
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"  Total Trades: {report['total_trades']}")
        print(f"  Winning Trades: {report['winning_trades']}")
        print(f"  Losing Trades: {report['losing_trades']}")
        print(f"  Win Rate: {report['win_rate']:.1f}%")
        print(f"  Total P&L: ₹{report['total_pnl']:,.2f}")
        print(f"  Avg Profit: ₹{report['avg_profit']:,.2f}")
        print(f"  Avg Loss: ₹{report['avg_loss']:,.2f}")
        print(f"  Profit Factor: {report['profit_factor']:.2f}")
        
        print(f"\n💰 PORTFOLIO:")
        print(f"  Ending Capital: ₹{report['ending_capital']:,.2f}")
        print(f"  Total P&L: ₹{report['total_portfolio_pnl']:,.2f}")
        
        print(f"\n📈 MARKET CONDITIONS:")
        print(f"  Nifty Close: {report['nifty_close']:,.2f}")
        print(f"  India VIX: {report['vix']:.2f}")
        
        if report['wins_analysis']:
            print(f"\n✅ WHAT WENT WELL:")
            for win in report['wins_analysis']:
                print(f"  {win}")
        
        if report['losses_analysis']:
            print(f"\n❌ WHAT WENT WRONG:")
            for loss in report['losses_analysis']:
                print(f"  {loss}")
        
        if report['key_learnings']:
            print(f"\n📚 KEY LEARNINGS:")
            for learning in report['key_learnings']:
                print(f"  • {learning}")
        
        print("\n" + "=" * 80 + "\n")
    
    def save_eod_report(self, report: Dict):
        """Save end-of-day report to database"""
        if not report:
            return
        
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO options_daily_analytics (
                    trade_date, total_trades, winning_trades, losing_trades, win_rate,
                    total_premium_paid, total_premium_received, avg_profit, avg_loss, profit_factor,
                    ending_capital, day_pnl, day_pnl_percent,
                    nifty_close, india_vix,
                    wins_analysis, losses_analysis, key_learnings
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (trade_date) DO UPDATE SET
                    total_trades = EXCLUDED.total_trades,
                    winning_trades = EXCLUDED.winning_trades,
                    profit_factor = EXCLUDED.profit_factor,
                    wins_analysis = EXCLUDED.wins_analysis,
                    losses_analysis = EXCLUDED.losses_analysis,
                    key_learnings = EXCLUDED.key_learnings
            """, (
                report['trade_date'],
                report['total_trades'],
                report['winning_trades'],
                report['losing_trades'],
                report['win_rate'],
                0,  # total_premium_paid (can calculate if needed)
                0,  # total_premium_received
                report['avg_profit'],
                report['avg_loss'],
                report['profit_factor'],
                report['ending_capital'],
                report['total_pnl'],
                0,  # day_pnl_percent
                report.get('nifty_close', 0),
                report.get('vix', 0),
                report['wins_analysis'],
                report['losses_analysis'],
                report['key_learnings']
            ))
            
            self.conn.commit()
            logger.info(f"EOD report saved for {report['trade_date']}")
            
        except Exception as e:
            logger.error(f"Error saving EOD report: {e}")
            self.conn.rollback()
        
        cursor.close()


if __name__ == "__main__":
    # Generate today's report
    analytics = OptionsAnalytics()
    report = analytics.generate_eod_report()
    
    analytics.print_eod_report(report)
    
    if report:
        analytics.save_eod_report(report)
