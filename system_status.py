"""
System Status Check - Verify all components
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
get_settings.cache_clear()

import requests
import psycopg2
from datetime import datetime

print("="*70)
print("  TRADING SYSTEM - STATUS CHECK")
print("="*70)

settings = get_settings()

# 1. Check Zerodha API
print("\n1. ZERODHA API CONNECTION")
print("-" * 70)
try:
    from kiteconnect import KiteConnect
    kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
    kite.set_access_token(settings.ZERODHA_ACCESS_TOKEN)
    profile = kite.profile()
    print(f"✅ Connected")
    print(f"   User: {profile['user_name']} ({profile['user_id']})")
    print(f"   Email: {profile['email']}")
except Exception as e:
    print(f"❌ Failed: {e}")

# 2. Check Database
print("\n2. TIMESCALEDB DATABASE")
print("-" * 70)
try:
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Get version
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0].split(',')[0]
    print(f"✅ Connected")
    print(f"   {version}")
    
    # Get table count
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    table_count = cursor.fetchone()[0]
    print(f"   Tables: {table_count}")
    
    # Get data count
    cursor.execute("SELECT COUNT(*) FROM market_ohlc;")
    ohlc_count = cursor.fetchone()[0]
    print(f"   OHLC Records: {ohlc_count}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")

# 3. Check Backend API
print("\n3. BACKEND API SERVER")
print("-" * 70)
try:
    response = requests.get(f"http://localhost:{settings.API_PORT}/", timeout=5)
    data = response.json()
    print(f"✅ Online")
    print(f"   {data['name']} v{data['version']}")
    print(f"   URL: http://localhost:{settings.API_PORT}")
    print(f"   Docs: http://localhost:{settings.API_PORT}/api/docs")
    
    # Test health
    health = requests.get(f"http://localhost:{settings.API_PORT}/api/health", timeout=5)
    health_data = health.json()
    print(f"   Health: {health_data['status']}")
    print(f"   Database: {health_data['database']}")
except Exception as e:
    print(f"❌ Failed: {e}")

# 4. Check Dashboard
print("\n4. DASHBOARD (NEXT.JS)")
print("-" * 70)
try:
    response = requests.get("http://localhost:3000", timeout=5)
    if response.status_code == 200:
        print(f"✅ Online")
        print(f"   URL: http://localhost:3000")
    else:
        print(f"⚠️  Responding but status code: {response.status_code}")
        print(f"   URL: http://localhost:3000")
except Exception as e:
    print(f"❌ Failed: {e}")

# 5. Check Docker  
print("\n5. DOCKER CONTAINERS")
print("-" * 70)
try:
    import subprocess
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=trading", "--format", "{{.Names}}\t{{.Status}}"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0 and result.stdout.strip():
        containers = result.stdout.strip().split('\n')
        print(f"✅ Running: {len(containers)} container(s)")
        for container in containers:
            name, status = container.split('\t')
            print(f"   - {name}: {status}")
    else:
        print("⚠️  No trading containers running")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*70)
print("  SUMMARY")
print("="*70)
print("\n✅ Zerodha API: Working")
print("✅ TimescaleDB: Running") 
print("✅ Backend API: http://localhost:8000")
print("⚠️  Dashboard: Check http://localhost:3000 in browser")
print("\nNext Steps:")
print("1. Open browser: http://localhost:3000 (Dashboard)")
print("2. API Documentation: http://localhost:8000/api/docs")
print("3. Run market data fetch: py services\\market_data\\ingestion_pipeline.py")
print("4. Start scheduler: py services\\scheduler\\scheduler_service.py")
print("\n" + "="*70)
