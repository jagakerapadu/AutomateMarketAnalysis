"""
Start the FastAPI backend server
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from config.settings import get_settings

    settings = get_settings()

    print("="*60)
    print("  Starting Trading System API Server")
    print("="*60)
    print(f"\nHost: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"\nAPI Docs: http://localhost:{settings.API_PORT}/api/docs")
    print(f"Health Check: http://localhost:{settings.API_PORT}/api/health")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")

    uvicorn.run(
        "services.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
