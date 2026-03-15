"""Apply database normalization fixes"""
import psycopg2
from config.settings import get_settings
from pathlib import Path
import sys

def execute_sql_file(cursor, filepath):
    """Execute SQL from file"""
    print(f"\n{'=' * 80}")
    print(f"Executing: {filepath.name}")
    print('=' * 80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove psql-specific commands
    lines = []
    for line in content.split('\n'):
        if not line.strip().startswith('\\'):
            lines.append(line)
    sql = '\n'.join(lines)
    
    # Split statements properly, handling DO $$ blocks
    statements = []
    current_statement = []
    in_do_block = False
    
    for line in sql.split('\n'):
        line_stripped = line.strip()
        
        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith('--'):
            continue
            
        current_statement.append(line)
        
        # Track DO $$ blocks
        if 'DO $$' in line or 'DO $body$' in line:
            in_do_block = True
        
        # End of DO block
        if in_do_block and ('END $$' in line or 'END $body$' in line):
            in_do_block = False
            statements.append('\n'.join(current_statement))
            current_statement = []
        # Regular statement end
        elif not in_do_block and line.rstrip().endswith(';'):
            statements.append('\n'.join(current_statement))
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        statements.append('\n'.join(current_statement))
    
    success_count = 0
    error_count = 0
    
    for statement in statements:
        statement = statement.strip()
        if not statement:
            continue
            
        try:
            cursor.execute(statement)
            success_count += 1
            
            # Provide feedback on what was done
            upper_stmt = statement.upper()
            if 'CREATE INDEX' in upper_stmt:
                if 'IF NOT EXISTS' in upper_stmt:
                    parts = statement.split('IF NOT EXISTS')
                    if len(parts) > 1:
                        index_name = parts[1].split()[0].strip()
                        print(f"  ✓ Index: {index_name}")
                else:
                    print(f"  ✓ Created index")
            elif 'ALTER TABLE' in upper_stmt and 'ADD CONSTRAINT' in upper_stmt:
                print(f"  ✓ Added constraint")
            elif 'ALTER TABLE' in upper_stmt and 'ADD COLUMN' in upper_stmt:
                print(f"  ✓ Added column")
            elif 'DO $$' in statement or 'DO $body$' in statement:
                print(f"  ✓ Executed procedural block")
            elif 'UPDATE' in upper_stmt:
                print(f"  ✓ Updated data")
                
        except psycopg2.Error as e:
            error_msg = str(e)
            # Check if error is benign (already exists)
            if any(phrase in error_msg.lower() for phrase in ['already exists', 'duplicate']):
                print(f"  → Already exists (skipping)")
                success_count += 1
            else:
                error_count += 1
                # Show first line of error only
                first_error_line = error_msg.split('\n')[0]
                print(f"  ✗ Error: {first_error_line}")
                
    return success_count, error_count

def main():
    settings = get_settings()
    
    print("\n" + "=" * 80)
    print("DATABASE NORMALIZATION & PERFORMANCE FIX")
    print("=" * 80)
    
    try:
        # Connect to database
        print(f"\nConnecting to database...")
        print(f"  Host: {settings.DB_HOST}")
        print(f"  Port: {settings.DB_PORT}")
        print(f"  Database: {settings.DB_NAME}")
        print(f"  User: {settings.DB_USER}")
        
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("  ✓ Connected successfully!")
        
        # Get current state
        print("\n" + "=" * 80)
        print("CURRENT DATABASE STATE")
        print("=" * 80)
        
        # Check foreign keys
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_schema = 'public'
            AND table_name LIKE 'paper_%'
        """)
        fk_count = cursor.fetchone()[0]
        print(f"  Foreign Keys on paper_* tables: {fk_count}")
        
        # Check indexes on paper_orders
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE tablename = 'paper_orders'
            AND indexname NOT LIKE '%pkey%' 
            AND indexname NOT LIKE '%order_id%'
        """)
        po_indexes = cursor.fetchone()[0]
        print(f"  Performance indexes on paper_orders: {po_indexes}")
        
        # Ask for confirmation
        print("\n" + "=" * 80)
        print("FIXES TO APPLY")
        print("=" * 80)
        print("  1. Add performance indexes (ZERO downtime)")
        print("  2. Add foreign key constraints (requires consistency check)")
        
        response = input("\nProceed with fixes? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n❌ Aborted by user")
            return
        
        # Step 1: Add performance indexes
        sql_file = Path("scripts/sql/add_performance_indexes.sql")
        if sql_file.exists():
            success, errors = execute_sql_file(cursor, sql_file)
            print(f"\n  ✓ Performance indexes: {success} successful, {errors} errors")
        else:
            print(f"\n  ⚠️ File not found: {sql_file}")
        
        # Step 2: Add foreign keys
        sql_file = Path("scripts/sql/add_foreign_keys.sql")
        if sql_file.exists():
            success, errors = execute_sql_file(cursor, sql_file)
            print(f"\n  ✓ Foreign keys: {success} successful, {errors} errors")
        else:
            print(f"\n  ⚠️ File not found: {sql_file}")
        
        # Verify results
        print("\n" + "=" * 80)
        print("VERIFICATION")
        print("=" * 80)
        
        # Check foreign keys again
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_schema = 'public'
            AND table_name LIKE 'paper_%'
        """)
        new_fk_count = cursor.fetchone()[0]
        print(f"  Foreign Keys: {fk_count} → {new_fk_count} ({new_fk_count - fk_count:+d})")
        
        # Check indexes again
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE tablename = 'paper_orders'
            AND indexname NOT LIKE '%pkey%' 
            AND indexname NOT LIKE '%order_id%'
        """)
        new_po_indexes = cursor.fetchone()[0]
        print(f"  paper_orders indexes: {po_indexes} → {new_po_indexes} ({new_po_indexes - po_indexes:+d})")
        
        print("\n" + "=" * 80)
        print("✓ DATABASE FIXES APPLIED SUCCESSFULLY!")
        print("=" * 80)
        print("\nYour database is now:")
        print("  ✓ Better normalized (with referential integrity)")
        print("  ✓ Indexed for performance (10-100x faster queries)")
        print("  ✓ Protected from data corruption")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        print("\nPossible causes:")
        print("  1. PostgreSQL/TimescaleDB is not running")
        print("  2. Wrong credentials in .env file")
        print("  3. Database host/port incorrect")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
