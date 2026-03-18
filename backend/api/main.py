"""Main FastAPI application for NeuroCommerce OS"""
import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional
import secrets
import string

from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, "/backend")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Models and database
try:
    from models.models import Base, Store, User, ApiKey
except ImportError as e:
    # Fallback for local development
    logger.warning(f"Could not import models from /backend: {e}")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from models.models import Base, Store, User, ApiKey
    except ImportError:
        logger.warning("Models import failed, will operate in degraded mode")
        Base = None
        Store = None
        User = None
        ApiKey = None

from database import engine, SessionLocal, init_db
from security import hash_password, verify_password, create_access_token, get_current_user
from routers import auth, events, agents, shopify, campaigns, experiments, billing

# Configuration
from config import (
    API_TITLE, API_DESCRIPTION, API_VERSION, API_LOG_LEVEL,
    CORS_ORIGINS, ALLOWED_HOSTS, STORE_ID_PREFIX, 
    API_HOST, API_PORT
)

# Update logging level from config
logging.getLogger().setLevel(API_LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting NeuroCommerce OS API...")
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    yield
    # Shutdown
    logger.info("Shutting down NeuroCommerce OS API...")


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)


# Request/Response Models
class StoreCreate(BaseModel):
    domain: str
    name: str
    shopify_store_id: str


class StoreResponse(BaseModel):
    id: str
    domain: str
    name: str
    plan: str
    subscription_status: str
    created_at: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    cache: str


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    try:
        # Check cache (Redis)
        from .cache import redis_client
        redis_client.ping()
        cache_status = "healthy"
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        cache_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" and cache_status == "healthy" else "degraded",
        version=API_VERSION,
        database=db_status,
        cache=cache_status
    )


# Store Management Endpoints
@app.post("/stores", response_model=StoreResponse)
async def create_store(store: StoreCreate, db: Session = Depends(get_db)):
    """Create a new store"""
    # Check if store already exists
    existing = db.query(Store).filter(Store.domain == store.domain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Store already exists")
    
    # Generate store ID
    store_id = f"{STORE_ID_PREFIX}{secrets.token_urlsafe(16)}"
    
    new_store = Store(
        id=store_id,
        domain=store.domain,
        name=store.name,
        shopify_store_id=store.shopify_store_id,
        shopify_access_token="",  # Will be set during OAuth
    )
    
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    
    logger.info(f"Created store: {store_id}")
    return StoreResponse.from_orm(new_store)


@app.get("/stores/{store_id}", response_model=StoreResponse)
async def get_store(store_id: str, db: Session = Depends(get_db)):
    """Get store details"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return StoreResponse.from_orm(store)


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(shopify.router, prefix="/api/v1/shopify", tags=["shopify"])
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["campaigns"])
app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
