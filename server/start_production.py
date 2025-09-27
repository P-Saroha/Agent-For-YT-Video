import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    workers = int(os.getenv("WORKERS", 1))
    
    # Production configuration
    config = {
        "app": app,
        "host": host,
        "port": port,
        "reload": debug,
        "access_log": True,
        "log_level": "info" if not debug else "debug"
    }
    
    # Add workers for production
    if not debug and workers > 1:
        config["workers"] = workers
    
    print(f"🚀 Starting YouTube AI Assistant...")
    print(f"📡 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"👥 Workers: {workers if not debug else 1}")
    
    uvicorn.run(**config)