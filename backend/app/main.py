"""
Main FastAPI application.
"""
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys

from app.config import settings
from app.utils.database import init_db
from app.routers import admin, public
from app.services.websocket_handler import handle_websocket


# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    level="DEBUG"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Real-Time Translation API...")
    
    # Initialize database
    await init_db()
    logger.success("Database initialized")
    
    # Optionally preload models here
    # translation_service.preload_models([("en", "hi"), ("en", "es")])
    
    logger.success("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Real-time speech translation API with control panel",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(public.router)
app.include_router(admin.router)


# WebSocket endpoint for real-time translation
@app.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket, request: Request):
    """
    WebSocket endpoint for real-time translation.
    
    Client should:
    1. Connect to this endpoint
    2. Send config message: {"type": "config", "source_lang": "en", "target_lang": "hi", ...}
    3. Send audio chunks as binary data
    4. Receive translation responses as JSON
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    await handle_websocket(websocket, client_ip, user_agent)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Real-Time Translation API",
        "version": settings.api_version,
        "docs": "/docs",
        "websocket": "/ws/translate"
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
