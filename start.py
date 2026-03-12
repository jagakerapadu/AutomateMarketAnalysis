"""Startup script - Initialize and start all services"""
import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║      TRADING SYSTEM - Hedge Fund Style Platform         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

def check_env_file():
    """Check if .env file exists"""
    if not Path(".env").exists():
        print("❌ Error: .env file not found!")
        print("📋 Please create .env file from .env.example")
        print("   Run: copy .env.example .env")
        sys.exit(1)
    print("✓ Environment file found")

def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import fastapi
        import pandas
        import sqlalchemy
        print("✓ Python dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("📦 Install with: pip install -r requirements.txt")
        sys.exit(1)

def check_database():
    """Check database connection"""
    try:
        from config.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✓ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("🔧 Please check your database configuration in .env")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    dirs = ["logs", "data/raw", "data/processed", "backtest_results"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✓ Directories created")

def start_api_server():
    """Start FastAPI backend"""
    print("\n🚀 Starting API server on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/api/docs\n")
    
    os.chdir("services/api")
    subprocess.Popen([sys.executable, "main.py"])
    os.chdir("../..")
    time.sleep(2)

def start_scheduler():
    """Start scheduler"""
    print("⏰ Starting scheduler...")
    subprocess.Popen([sys.executable, "scheduler/scheduler.py"])
    time.sleep(1)

def start_dashboard():
    """Start Next.js dashboard"""
    print("\n🎨 Starting dashboard on http://localhost:3000\n")
    os.chdir("dashboard")
    subprocess.Popen(["npm", "run", "dev"], shell=True)
    os.chdir("..")

def main():
    """Main startup function"""
    print_banner()
    
    print("🔍 Running system checks...\n")
    check_env_file()
    check_dependencies()
    check_database()
    create_directories()
    
    print("\n✅ All checks passed!\n")
    print("=" * 60)
    print("Starting services...")
    print("=" * 60)
    
    # Start backend
    start_api_server()
    
    # Start scheduler
    start_scheduler()
    
    # Start dashboard
    print("\n⚠️  To start the dashboard, run in a separate terminal:")
    print("   cd dashboard")
    print("   npm run dev")
    
    print("\n" + "=" * 60)
    print("✅ Trading System is running!")
    print("=" * 60)
    print("\n📊 Access points:")
    print("   • API:       http://localhost:8000")
    print("   • API Docs:  http://localhost:8000/api/docs")
    print("   • Dashboard: http://localhost:3000 (if started)")
    print("\n⏸️  Press Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...\n")
        print("✅ System stopped successfully")

if __name__ == "__main__":
    main()
