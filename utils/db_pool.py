"""
Database Connection Pool - Better performance and connection management
"""
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional
from config.settings import get_settings
from config.logger import setup_logger

logger = setup_logger("db_pool")


class DatabasePool:
    """Singleton connection pool for PostgreSQL"""
    
    _instance: Optional['DatabasePool'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize connection pool"""
        if self._pool is None:
            settings = get_settings()
            
            try:
                # Create threaded connection pool
                # minconn=1, maxconn=10 for trading application
                self._pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    # Connection timeout settings
                    connect_timeout=5,
                    # Keep connections alive
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
                logger.info("Database connection pool initialized (1-10 connections)")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise
    
    def get_connection(self):
        """
        Get a connection from the pool
        
        Returns:
            Database connection
        
        Raises:
            pool.PoolError: If no connections available
        """
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        
        try:
            conn = self._pool.getconn()
            logger.debug("Connection acquired from pool")
            return conn
        except pool.PoolError as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise
    
    def return_connection(self, conn):
        """
        Return connection to the pool
        
        Args:
            conn: Database connection to return
        """
        if self._pool is None:
            return
        
        try:
            self._pool.putconn(conn)
            logger.debug("Connection returned to pool")
        except pool.PoolError as e:
            logger.error(f"Failed to return connection to pool: {e}")
    
    def close_all(self):
        """Close all connections in the pool"""
        if self._pool is not None:
            self._pool.closeall()
            logger.info("All database connections closed")
            self._pool = None
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """
        Context manager for database operations
        
        Usage:
            with db_pool.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO ...")
                # Auto-commits if commit=True
                # Auto-rollback on exception
        
        Args:
            commit: Whether to commit after operation
        
        Yields:
            Database cursor
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            yield cursor
            
            if commit:
                conn.commit()
                logger.debug("Transaction committed")
        
        except Exception as e:
            if conn:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
            raise
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)


# Global singleton instance
_db_pool = None


def get_db_pool() -> DatabasePool:
    """
    Get global database pool instance
    
    Returns:
        DatabasePool singleton
    """
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool()
    return _db_pool


def close_db_pool():
    """Close global database pool"""
    global _db_pool
    if _db_pool is not None:
        _db_pool.close_all()
        _db_pool = None


@contextmanager
def transaction():
    """
    Context manager for database transactions
    
    Usage:
        with transaction() as cursor:
            cursor.execute("INSERT INTO ...")
            cursor.execute("UPDATE ...")
        # Auto-commits if successful, auto-rollback on error
    
    Yields:
        Database cursor
    """
    pool = get_db_pool()
    with pool.get_cursor(commit=True) as cursor:
        yield cursor
