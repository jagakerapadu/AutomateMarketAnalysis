-- =============================================================================
-- ADD FOREIGN KEY CONSTRAINTS
-- =============================================================================
-- Purpose: Add referential integrity to prevent data corruption
-- Impact: Prevents orphaned records, enables cascade deletes
-- Downtime: 5-10 minutes (run during non-market hours)
-- Safe to run: YES (but backup database first)
-- =============================================================================

-- IMPORTANT: Run this during non-market hours (after 3:30 PM or weekends)
-- BACKUP DATABASE FIRST!

\echo '=============================================================================='
\echo 'PRE-FLIGHT CHECK'
\echo '=============================================================================='

-- Check current foreign keys (should be none)
SELECT 
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public'
  AND tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name LIKE 'paper_%';

\echo ''
\echo 'If no rows above, proceeding with FK creation...'
\echo ''

-- =============================================================================
-- STEP 1: Add portfolio_id columns (if not exists)
-- =============================================================================

\echo '=============================================================================='
\echo 'STEP 1: Adding portfolio_id columns to child tables...'
\echo '=============================================================================='

DO $$
BEGIN
    -- Add portfolio_id to paper_positions
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'paper_positions' AND column_name = 'portfolio_id'
    ) THEN
        ALTER TABLE paper_positions ADD COLUMN portfolio_id INTEGER;
        RAISE NOTICE '  ✓ Added portfolio_id to paper_positions';
    ELSE
        RAISE NOTICE '  → portfolio_id already exists in paper_positions';
    END IF;
    
    -- Add portfolio_id to paper_orders
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'paper_orders' AND column_name = 'portfolio_id'
    ) THEN
        ALTER TABLE paper_orders ADD COLUMN portfolio_id INTEGER;
        RAISE NOTICE '  ✓ Added portfolio_id to paper_orders';
    ELSE
        RAISE NOTICE '  → portfolio_id already exists in paper_orders';
    END IF;
END $$;

-- =============================================================================
-- STEP 2: Set portfolio_id = 1 for all existing records
-- =============================================================================

\echo ''
\echo '=============================================================================='
\echo 'STEP 2: Setting portfolio_id = 1 for existing records...'
\echo '=============================================================================='

UPDATE paper_positions SET portfolio_id = 1 WHERE portfolio_id IS NULL;
UPDATE paper_orders SET portfolio_id = 1 WHERE portfolio_id IS NULL;

\echo '  ✓ Updated paper_positions'
\echo '  ✓ Updated paper_orders'

-- =============================================================================
-- STEP 3: Make portfolio_id NOT NULL
-- =============================================================================

\echo ''
\echo '=============================================================================='
\echo 'STEP 3: Making portfolio_id mandatory...'
\echo '=============================================================================='

ALTER TABLE paper_positions ALTER COLUMN portfolio_id SET NOT NULL;
ALTER TABLE paper_orders ALTER COLUMN portfolio_id SET NOT NULL;

\echo '  ✓ paper_positions.portfolio_id is now NOT NULL'
\echo '  ✓ paper_orders.portfolio_id is now NOT NULL'

-- =============================================================================
-- STEP 4: Ensure paper_portfolio has id = 1
-- =============================================================================

\echo ''
\echo '=============================================================================='
\echo 'STEP 4: Verifying paper_portfolio record exists...'
\echo '=============================================================================='

DO $$
DECLARE
    portfolio_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO portfolio_count FROM paper_portfolio WHERE id = 1;
    
    IF portfolio_count = 0 THEN
        -- Create default portfolio if doesn't exist
        INSERT INTO paper_portfolio (id, total_capital, available_cash, invested_amount, total_pnl, today_pnl)
        VALUES (1, 1000000, 1000000, 0, 0, 0)
        ON CONFLICT (id) DO NOTHING;
        RAISE NOTICE '  ✓ Created default portfolio (id=1) with ₹10,00,000 capital';
    ELSE
        RAISE NOTICE '  → paper_portfolio already has record with id=1';
    END IF;
END $$;

-- =============================================================================
-- STEP 5: Add foreign key constraints
-- =============================================================================

\echo ''
\echo '=============================================================================='
\echo 'STEP 5: Adding foreign key constraints...'
\echo '=============================================================================='

-- FK 1: paper_positions → paper_portfolio
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_paper_positions_portfolio'
    ) THEN
        ALTER TABLE paper_positions
            ADD CONSTRAINT fk_paper_positions_portfolio
            FOREIGN KEY (portfolio_id) 
            REFERENCES paper_portfolio(id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
        RAISE NOTICE '  ✓ Added FK: paper_positions.portfolio_id → paper_portfolio.id';
    ELSE
        RAISE NOTICE '  → FK already exists: fk_paper_positions_portfolio';
    END IF;
END $$;

-- FK 2: paper_orders → paper_portfolio
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_paper_orders_portfolio'
    ) THEN
        ALTER TABLE paper_orders
            ADD CONSTRAINT fk_paper_orders_portfolio
            FOREIGN KEY (portfolio_id) 
            REFERENCES paper_portfolio(id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
        RAISE NOTICE '  ✓ Added FK: paper_orders.portfolio_id → paper_portfolio.id';
    ELSE
        RAISE NOTICE '  → FK already exists: fk_paper_orders_portfolio';
    END IF;
END $$;

-- FK 3: paper_orders → signals (optional - allows NULL)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_paper_orders_signal'
    ) THEN
        ALTER TABLE paper_orders
            ADD CONSTRAINT fk_paper_orders_signal
            FOREIGN KEY (signal_id) 
            REFERENCES signals(id)
            ON DELETE SET NULL  -- Keep order history even if signal deleted
            ON UPDATE CASCADE;
        RAISE NOTICE '  ✓ Added FK: paper_orders.signal_id → signals.id (ON DELETE SET NULL)';
    ELSE
        RAISE NOTICE '  → FK already exists: fk_paper_orders_signal';
    END IF;
END $$;

-- =============================================================================
-- STEP 6: Create indexes on foreign key columns (for join performance)
-- =============================================================================

\echo ''
\echo '=============================================================================='
\echo 'STEP 6: Adding indexes on foreign key columns...'
\echo '=============================================================================='

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_positions_portfolio 
    ON paper_positions (portfolio_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_portfolio 
    ON paper_orders (portfolio_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_paper_orders_signal 
    ON paper_orders (signal_id) 
    WHERE signal_id IS NOT NULL;

\echo '  ✓ Created: idx_paper_positions_portfolio'
\echo '  ✓ Created: idx_paper_orders_portfolio'
\echo '  ✓ Created: idx_paper_orders_signal'

-- =============================================================================
-- VERIFICATION
-- =============================================================================

\echo ''
\echo '=============================================================================='
\echo 'VERIFICATION: Foreign Key Constraints Added'
\echo '=============================================================================='

SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS references_table,
    ccu.column_name AS references_column,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
  AND tc.table_name LIKE 'paper_%'
ORDER BY tc.table_name;

\echo ''
\echo '=============================================================================='
\echo 'TEST FOREIGN KEY CONSTRAINTS'
\echo '=============================================================================='
\echo 'Testing FK enforcement...'
\echo ''

-- Test 1: Try to insert order with invalid signal_id (should fail)
\echo 'Test 1: Attempting to insert order with invalid signal_id=999999...'
DO $$
BEGIN
    INSERT INTO paper_orders (order_id, portfolio_id, symbol, order_type, quantity, price, status, signal_id)
    VALUES ('TEST_FK_1', 1, 'TEST', 'BUY', 10, 100, 'PENDING', 999999);
    RAISE EXCEPTION 'ERROR: FK constraint should have prevented this!';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE '  ✅ PASS: FK correctly rejected invalid signal_id';
    WHEN OTHERS THEN
        RAISE NOTICE '  ❌ FAIL: Unexpected error';
END $$;

-- Test 2: Try to insert position with invalid portfolio_id (should fail)
\echo 'Test 2: Attempting to insert position with invalid portfolio_id=999...'
DO $$
BEGIN
    INSERT INTO paper_positions (portfolio_id, symbol, quantity, avg_price, invested_value)
    VALUES (999, 'TEST', 10, 100, 1000);
    RAISE EXCEPTION 'ERROR: FK constraint should have prevented this!';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE '  ✅ PASS: FK correctly rejected invalid portfolio_id';
    WHEN OTHERS THEN
        RAISE NOTICE '  ❌ FAIL: Unexpected error';
END $$;

\echo ''
\echo '=============================================================================='
\echo '✅ FOREIGN KEY CONSTRAINTS SUCCESSFULLY ADDED!'
\echo '=============================================================================='
\echo 'Benefits:'
\echo '  • Prevents orphaned records (orders without valid portfolio)'
\echo '  • Automatic cleanup (cascade delete)'
\echo '  • Data integrity guaranteed by database'
\echo ''
\echo 'Next steps:'
\echo '1. Run regression tests: py run_all_tests.py'
\echo '2. Test application: py start_paper_trading.py'
\echo '3. Monitor logs for any FK violations'
\echo '=============================================================================='
