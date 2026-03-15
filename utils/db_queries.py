"""
SQL Query Constants - Centralized query definitions for better maintainability
"""

# ============================================================================
# PAPER TRADING QUERIES
# ============================================================================

# Portfolio Queries
GET_PORTFOLIO = """
    SELECT 
        portfolio_id,
        initial_capital,
        current_balance,
        invested_amount,
        total_pnl,
        total_pnl_percent,
        updated_at
    FROM paper_portfolio
    WHERE portfolio_id = %s
"""

UPDATE_PORTFOLIO_BALANCE = """
    UPDATE paper_portfolio
    SET 
        current_balance = current_balance + %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE portfolio_id = %s
"""

UPDATE_PORTFOLIO_STATS = """
    UPDATE paper_portfolio
    SET 
        current_balance = %s,
        invested_amount = %s,
        total_pnl = %s,
        total_pnl_percent = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE portfolio_id = %s
"""

# Position Queries
GET_ALL_POSITIONS = """
    SELECT
        position_id,
        symbol,
        quantity,
        avg_price,
        current_price,
        last_updated,
        current_value,
        pnl,
        pnl_percent
    FROM paper_positions
    WHERE portfolio_id = %s
    ORDER BY symbol
"""

GET_POSITION_BY_SYMBOL = """
    SELECT
        position_id,
        symbol,
        quantity,
        avg_price,
        current_price,
        last_updated
    FROM paper_positions
    WHERE portfolio_id = %s AND symbol = %s
"""

INSERT_POSITION = """
    INSERT INTO paper_positions
        (portfolio_id, symbol, quantity, avg_price, current_price, last_updated)
    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
"""

UPDATE_POSITION = """
    UPDATE paper_positions
    SET
        quantity = %s,
        avg_price = %s,
        last_updated = CURRENT_TIMESTAMP
    WHERE position_id = %s
"""

UPDATE_POSITION_PRICE = """
    UPDATE paper_positions
    SET
        current_price = %s,
        current_value = quantity * %s,
        pnl = (quantity * %s) - (quantity * avg_price),
        pnl_percent = CASE 
            WHEN avg_price > 0 THEN ((%s - avg_price) / avg_price) * 100
            ELSE 0
        END,
        last_updated = CURRENT_TIMESTAMP
    WHERE position_id = %s
"""

DELETE_POSITION = """
    DELETE FROM paper_positions
    WHERE position_id = %s
"""

# Order Queries
INSERT_ORDER = """
    INSERT INTO paper_orders
        (order_id, portfolio_id, symbol, order_type, quantity, price, status, signal_id, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
"""

GET_ORDER_HISTORY = """
    SELECT
        order_id,
        symbol,
        order_type,
        quantity,
        price,
        status,
        created_at,
        signal_id
    FROM paper_orders
    WHERE portfolio_id = %s
    ORDER BY created_at DESC
    LIMIT %s
"""

GET_ORDERS_BY_SYMBOL = """
    SELECT
        order_id,
        order_type,
        quantity,
        price,
        status,
        created_at
    FROM paper_orders
    WHERE portfolio_id = %s AND symbol = %s
    ORDER BY created_at DESC
"""

UPDATE_ORDER_STATUS = """
    UPDATE paper_orders
    SET 
        status = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE order_id = %s
"""

# ============================================================================
# SIGNAL QUERIES
# ============================================================================

GET_PENDING_SIGNALS = """
    SELECT
        signal_id,
        symbol,
        action,
        entry_price,
        current_price,
        stop_loss,
        target,
        quantity,
        risk_reward_ratio,
        status,
        created_at,
        updated_at
    FROM signals
    WHERE status = 'PENDING'
    ORDER BY created_at
"""

GET_ACTIVE_SIGNALS = """
    SELECT
        signal_id,
        symbol,
        action,
        entry_price,
        current_price,
        stop_loss,
        target,
        quantity,
        status
    FROM signals
    WHERE status = 'ACTIVE'
    ORDER BY symbol
"""

UPDATE_SIGNAL_STATUS = """
    UPDATE signals
    SET
        status = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE signal_id = %s
"""

UPDATE_SIGNAL_CURRENT_PRICE = """
    UPDATE signals
    SET
        current_price = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE signal_id = %s
"""

INSERT_SIGNAL = """
    INSERT INTO signals
        (symbol, action, entry_price, current_price, stop_loss, target, 
         quantity, risk_reward_ratio, status, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
"""

DELETE_OLD_SIGNALS = """
    DELETE FROM signals
    WHERE status = 'CLOSED' 
    AND updated_at < NOW() - INTERVAL '%s days'
"""

# ============================================================================
# PORTFOLIO STATISTICS QUERIES
# ============================================================================

GET_PORTFOLIO_STATS = """
    SELECT
        COUNT(*) as total_positions,
        SUM(quantity * avg_price) as total_invested,
        SUM(current_value) as total_current_value,
        SUM(pnl) as total_pnl
    FROM paper_positions
    WHERE portfolio_id = %s
"""

GET_ORDER_STATS = """
    SELECT
        COUNT(*) as total_orders,
        COUNT(CASE WHEN order_type = 'BUY' THEN 1 END) as buy_orders,
        COUNT(CASE WHEN order_type = 'SELL' THEN 1 END) as sell_orders,
        COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_orders,
        SUM(CASE WHEN order_type = 'BUY' THEN quantity * price ELSE 0 END) as total_bought,
        SUM(CASE WHEN order_type = 'SELL' THEN quantity * price ELSE 0 END) as total_sold
    FROM paper_orders
    WHERE portfolio_id = %s
    AND created_at >= %s
"""

GET_TOP_PERFORMERS = """
    SELECT
        symbol,
        quantity,
        avg_price,
        current_price,
        pnl,
        pnl_percent
    FROM paper_positions
    WHERE portfolio_id = %s
    ORDER BY pnl_percent DESC
    LIMIT %s
"""

GET_TOP_LOSERS = """
    SELECT
        symbol,
        quantity,
        avg_price,
        current_price,
        pnl,
        pnl_percent
    FROM paper_positions
    WHERE portfolio_id = %s
    ORDER BY pnl_percent ASC
    LIMIT %s
"""

# ============================================================================
# ADMIN/MAINTENANCE QUERIES
# ============================================================================

CLEANUP_STALE_POSITIONS = """
    DELETE FROM paper_positions
    WHERE quantity = 0
    AND last_updated < NOW() - INTERVAL '7 days'
"""

GET_POSITIONS_WITHOUT_PRICE = """
    SELECT
        position_id,
        symbol,
        quantity,
        avg_price
    FROM paper_positions
    WHERE current_price IS NULL
    OR last_updated < NOW() - INTERVAL '1 hour'
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_query(query_name: str) -> str:
    """
    Get a query by name (for dynamic query selection)
    
    Args:
        query_name: Name of the query constant
    
    Returns:
        SQL query string
    
    Raises:
        KeyError: If query name not found
    """
    return globals().get(query_name)
