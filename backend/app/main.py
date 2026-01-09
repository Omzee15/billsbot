"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from contextlib import asynccontextmanager

from database import init_db
from routers import webhook, bills

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting BillBot application...")
    
    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
    
    # Create necessary folders
    os.makedirs("/app/bills", exist_ok=True)
    os.makedirs("/app/exports", exist_ok=True)
    logger.info("Data folders created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BillBot application...")


# Create FastAPI app
app = FastAPI(
    title="BillBot API",
    description="AI-powered bill management system with Telegram integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook.router)
app.include_router(bills.router)


@app.get("/")
async def root():
    """
    Root endpoint - health check
    """
    return {
        "status": "running",
        "service": "BillBot API",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/telegram",
            "bills": "/bills/*",
            "export": "/bills/export/{user_id}",
            "email": "/bills/email/send"
        }
    }


@app.get("/health")
@app.head("/health")
async def health_check():
    """
    Health check endpoint (supports GET and HEAD requests)
    """
    return {
        "status": "healthy",
        "database": "connected",
        "services": ["telegram", "ocr", "export", "email"]
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("APP_PORT", 8000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )
