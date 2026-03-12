"""
Position Analysis Module - Analyzes open positions to identify issues and provide recommendations
"""
import psycopg2
from datetime import datetime, timezone
from typing import Dict, List, Any
from config.settings import get_settings


class PositionAnalyzer:
    """Analyzes open trading positions to identify what's going wrong"""
    
    def __init__(self):
        self.settings = get_settings()
        
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.settings.DB_HOST,
            port=self.settings.DB_PORT,
            database=self.settings.DB_NAME,
            user=self.settings.DB_USER,
            password=self.settings.DB_PASSWORD
        )
    
    def analyze_position(self, position_id: int) -> Dict[str, Any]:
        """
        Analyze a single position and identify what's going wrong
        
        Returns dict with:
        - position_details
        - signal_details  
        - issues: List of problems identified
        - recommendations: List of suggested actions
        - analysis: Overall assessment
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get position details
            cursor.execute("""
                SELECT 
                    p.id, p.symbol, p.quantity, p.avg_price, p.current_price,
                    p.pnl, p.pnl_percent, p.opened_at,
                    o.order_id, o.signal_id
                FROM paper_positions p
                JOIN paper_orders o ON p.symbol = o.symbol AND o.order_type = 'BUY'
                WHERE p.id = %s
            """, (position_id,))
            
            pos = cursor.fetchone()
            if not pos:
                return {"error": "Position not found"}
            
            pos_id, symbol, qty, entry, current, pnl, pnl_pct, opened_at, order_id, signal_id = pos
            
            # Calculate duration
            duration_hours = (datetime.now(timezone.utc) - opened_at).total_seconds() / 3600
            
            position_details = {
                "id": pos_id,
                "symbol": symbol,
                "quantity": qty,
                "entry_price": float(entry),
                "current_price": float(current) if current else float(entry),
                "pnl": float(pnl) if pnl else 0,
                "pnl_percent": float(pnl_pct) if pnl_pct else 0,
                "invested": float(entry * qty),
                "current_value": float(current * qty) if current else float(entry * qty),
                "opened_at": opened_at.isoformat(),
                "duration_hours": round(duration_hours, 1),
                "duration_days": round(duration_hours / 24, 1)
            }
            
            signal_details = None
            issues = []
            recommendations = []
            overall_assessment = "REVIEWING"
            
            # Get signal details if available
            if signal_id:
                cursor.execute("""
                    SELECT 
                        signal_type, strategy, confidence, entry_price,
                        target_price, stop_loss, reason, created_at
                    FROM signals
                    WHERE id = %s
                """, (signal_id,))
                
                signal = cursor.fetchone()
                if signal:
                    sig_type, strategy, conf, sig_entry, target, sl, reason, sig_time = signal
                    
                    # Calculate metrics
                    potential_gain = float(target - sig_entry)
                    potential_loss = float(sig_entry - sl)
                    risk_reward = abs(potential_gain / potential_loss) if potential_loss != 0 else 0
                    
                    current_loss_pct = abs(float(pnl_pct) if pnl_pct else 0)
                    sl_distance_pct = abs(((float(sl) / float(sig_entry)) - 1) * 100)
                    sl_proximity = (current_loss_pct / sl_distance_pct) * 100 if sl_distance_pct > 0 else 0
                    
                    signal_details = {
                        "type": sig_type,
                        "strategy": strategy,
                        "confidence": float(conf),
                        "entry_price": float(sig_entry),
                        "target_price": float(target),
                        "stop_loss": float(sl),
                        "reason": reason,
                        "risk_reward": round(risk_reward, 2),
                        "target_pct": round(((float(target)/float(sig_entry))-1)*100, 2),
                        "sl_pct": round(((float(sl)/float(sig_entry))-1)*100, 2),
                        "sl_proximity_pct": round(sl_proximity, 0)
                    }
                    
                    # Analyze issues
                    if conf < 70:
                        issues.append({
                            "severity": "HIGH",
                            "type": "LOW_CONFIDENCE",
                            "description": f"Signal confidence was only {conf:.0f}%",
                            "lesson": "Should only trade signals with ≥70% confidence"
                        })
                    elif conf < 80:
                        issues.append({
                            "severity": "MEDIUM",
                            "type": "MODERATE_CONFIDENCE",
                            "description": f"Signal confidence was {conf:.0f}%",
                            "lesson": "Consider requiring ≥80% confidence for better success rate"
                        })
                    
                    if risk_reward < 1.5:
                        issues.append({
                            "severity": "HIGH",
                            "type": "POOR_RISK_REWARD",
                            "description": f"Risk:Reward was only 1:{risk_reward:.2f}",
                            "lesson": "Don't take trades with R:R below 1:2"
                        })
                    
                    if duration_hours > 24 and current_loss_pct > 0.3:
                        issues.append({
                            "severity": "MEDIUM",
                            "type": "HELD_TOO_LONG",
                            "description": f"Position held for {duration_hours/24:.1f} days without profit",
                            "lesson": "Exit losing positions within 24 hours if no movement"
                        })
                    
                    if sig_type == 'BUY' and pnl_pct < 0:
                        issues.append({
                            "severity": "HIGH",
                            "type": "MARKET_AGAINST_US",
                            "description": "Entered BUY but price fell",
                            "lesson": "Market may be in downtrend - verify trend before entry"
                        })
                    
                    # Generate recommendations based on SL proximity
                    if sl_proximity >= 100:
                        recommendations.append({
                            "priority": "CRITICAL",
                            "action": "EXIT_IMMEDIATELY",
                            "description": f"Stop loss already hit at ₹{sl:.2f}",
                            "reason": "Protecting capital from further loss"
                        })
                        overall_assessment = "EXIT_NOW"
                    elif sl_proximity >= 90:
                        recommendations.append({
                            "priority": "HIGH",
                            "action": "EXIT_ASAP",
                            "description": f"Very close to stop loss ₹{sl:.2f}",
                            "reason": f"High risk of {-(sl_distance_pct - current_loss_pct):.2f}% further loss"
                        })
                        overall_assessment = "EXIT_SOON"
                    elif sl_proximity >= 70:
                        recommendations.append({
                            "priority": "MEDIUM",
                            "action": "WATCH_CLOSELY",
                            "description": "Monitor price action, approaching stop loss",
                            "reason": f"Exit if breaks below ₹{sl:.2f}"
                        })
                        overall_assessment = "MONITOR"
                    elif duration_hours > 48 and pnl_pct < -0.5:
                        recommendations.append({
                            "priority": "MEDIUM",
                            "action": "CONSIDER_EXIT",
                            "description": "No movement for 2+ days",
                            "reason": "Capital could be better deployed elsewhere"
                        })
                        overall_assessment = "CONSIDER_EXIT"
                    elif conf < 70:
                        recommendations.append({
                            "priority": "MEDIUM",
                            "action": "CONSIDER_EXIT",
                            "description": "Low confidence signal unlikely to recover",
                            "reason": f"Only {conf:.0f}% confident"
                        })
                        overall_assessment = "CONSIDER_EXIT"
                    else:
                        recommendations.append({
                            "priority": "LOW",
                            "action": "HOLD",
                            "description": f"Monitor but can still recover {abs(((float(target)/float(current))-1)*100):.2f}% to hit target",
                            "reason": f"Set strict stop loss at ₹{sl:.2f}"
                        })
                        overall_assessment = "HOLD"
            
            return {
                "position": position_details,
                "signal": signal_details,
                "issues": issues,
                "recommendations": recommendations,
                "assessment": overall_assessment
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def analyze_all_positions(self) -> Dict[str, Any]:
        """Analyze all open positions"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all position IDs sorted by loss
            cursor.execute("""
                SELECT id, symbol, pnl_percent
                FROM paper_positions
                ORDER BY pnl_percent ASC
            """)
            
            positions = cursor.fetchall()
            
            analyses = []
            total_loss = 0
            
            for pos_id, symbol, pnl_pct in positions:
                analysis = self.analyze_position(pos_id)
                analyses.append(analysis)
                total_loss += analysis["position"]["pnl"]
            
            # Generate overall summary
            common_issues = {}
            for analysis in analyses:
                for issue in analysis.get("issues", []):
                    issue_type = issue["type"]
                    if issue_type not in common_issues:
                        common_issues[issue_type] = {
                            "count": 0,
                            "description": issue["description"],
                            "lesson": issue["lesson"],
                            "severity": issue["severity"]
                        }
                    common_issues[issue_type]["count"] += 1
            
            # Sort by frequency
            top_issues = sorted(
                [{"type": k, **v} for k, v in common_issues.items()],
                key=lambda x: (-x["count"], x["severity"])
            )
            
            return {
                "total_positions": len(positions),
                "total_unrealized_loss": round(total_loss, 2),
                "positions": analyses,
                "common_issues": top_issues,
                "key_lessons": [
                    "Review market trend before taking BUY signals",
                    "Only trade high confidence signals (≥75%)",
                    "Verify risk:reward is at least 1:2",
                    "Set and follow strict stop losses",
                    "Exit losing positions quickly (within 24 hours if no movement)"
                ]
            }
            
        finally:
            cursor.close()
            conn.close()
