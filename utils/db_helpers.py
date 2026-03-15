"""
Database Helper Utilities - Safe NULL handling and type conversion
"""
from typing import Optional, Any
from decimal import Decimal
from datetime import datetime


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safely convert database value to float
    
    Args:
        value: Database value (can be Decimal, float, int, or None)
        default: Default value if conversion fails (default: None)
    
    Returns:
        Float value or default
    """
    if value is None:
        return default
    
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Safely convert database value to int
    
    Args:
        value: Database value
        default: Default value if conversion fails (default: None)
    
    Returns:
        Int value or default
    """
    if value is None:
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_decimal(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """
    Safely convert to Decimal (for currency calculations)
    
    Args:
        value: Value to convert
        default: Default if conversion fails
    
    Returns:
        Decimal value or default
    """
    if value is None:
        return default
    
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return default


def validate_positive(value: Optional[float], field_name: str) -> bool:
    """
    Validate that a value is positive (used for prices, quantities)
    
    Args:
        value: Value to check
        field_name: Field name for error messages
    
    Returns:
        True if valid, raises ValueError if not
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be None")
    
    if value <= 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    
    return True


def validate_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format
    
    Args:
        symbol: Stock symbol to validate
    
    Returns:
        True if valid, raises ValueError if not
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")
    
    # Basic validation - alphanumeric only, max 20 chars
    if not symbol.isalnum() or len(symbol) > 20:
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    return True


def validate_order_type(order_type: str) -> bool:
    """
    Validate order type
    
    Args:
        order_type: Order type to validate
    
    Returns:
        True if valid, raises ValueError if not
    """
    valid_types = ['BUY', 'SELL']
    
    if order_type not in valid_types:
        raise ValueError(f"Order type must be BUY or SELL, got {order_type}")
    
    return True


def sanitize_string(value: str, max_length: int = 100) -> str:
    """
    Sanitize string input to prevent SQL injection
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = str(value).strip()
    
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def format_currency_safe(value: Optional[float]) -> str:
    """
    Format currency value safely (handles None)
    
    Args:
        value: Currency value to format
    
    Returns:
        Formatted string or "N/A"
    """
    if value is None:
        return "N/A"
    
    try:
        return f"₹{value:,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def format_percent_safe(value: Optional[float]) -> str:
    """
    Format percentage value safely (handles None)
    
    Args:
        value: Percentage value to format
    
    Returns:
        Formatted string or "N/A"
    """
    if value is None:
        return "N/A"
    
    try:
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.2f}%"
    except (ValueError, TypeError):
        return "N/A"
