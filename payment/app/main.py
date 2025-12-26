"""FastAPI application entry point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from payment.app.config import settings
import redis
from payment.app.database import init_db
from payment.app.routers import orders_router
from payment.app.core.logging import setup_logging

logger = setup_logging("payment-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting payment service...")
    init_db()
    logger.info("Database initialized successfully")
    
    # Initialize Redis connection and store in app state
    app.state.redis = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    
    # Test connection
    try:
        app.state.redis.ping()
        logger.info(f"Redis connection established at {settings.redis_host}:{settings.redis_port}")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    yield
    
    # Shutdown - close Redis connection
    logger.info("Shutting down payment service...")
    if hasattr(app.state, 'redis'):
        try:
            app.state.redis.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Include routers
app.include_router(orders_router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.app_name}

