import os
import uvicorn

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    workers = int(os.getenv("WORKERS", 1))
    
    # Production configuration
    if debug:
        # Development mode - use import string for reload
        config = {
            "app": "app.main:app",  # Import string instead of app object
            "host": host,
            "port": port,
            "reload": True,
            "access_log": True,
            "log_level": "debug"
        }
    else:
        # Production mode - import app object for better performance
        from app.main import app
        config = {
            "app": app,
            "host": host,
            "port": port,
            "reload": False,
            "access_log": True,
            "log_level": "info"
        }
        # Add workers for production
        if workers > 1:
            config["workers"] = workers
    
    print(f"🚀 Starting YouTube AI Assistant...")
    print(f"📡 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"👥 Workers: {workers if not debug else 1}")
    
    uvicorn.run(**config)