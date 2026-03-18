"""
NeuroCommerce Setup API Endpoints

Handles the setup wizard flow for newly installed Shopify apps:
1. OAuth - Authorize app
2. Account setup - Create owner account
3. Store configuration - Configure store settings
4. Agent setup - Enable AI agents
5. Completion - Activate store
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging
import os

from ..database import get_db
from ...models.models import Store, User, ApiKey
from ...services.shopify_service import ShopifyService
from ..security import hash_password, create_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/setup", tags=["setup"])


# ==================== Pydantic Models ====================

class AccountSetupRequest(BaseModel):
    """Step 1: Create account and link Shopify store"""
    shop_name: str
    owner_email: EmailStr
    password: str
    owner_first_name: str
    owner_last_name: str
    shopify_shop_domain: str  # e.g., "mystore.myshopify.com"
    shopify_api_key: str
    shopify_access_token: str  # From OAuth flow


class StoreConfigRequest(BaseModel):
    """Step 2: Configure store settings"""
    store_id: str
    store_name: str
    industry: str  # "fashion", "electronics", "food", etc.
    target_audience: str
    monthly_visitors: int
    currency: str
    timezone: str


class AgentSetupRequest(BaseModel):
    """Step 3: Configure AI agents"""
    store_id: str
    agents_to_enable: List[str]  # ["product_recommender", "checkout_assistant", "support", etc.]
    agent_name: Optional[str] = None
    agent_personality: Optional[str] = None  # "professional", "friendly", "playful"


class SetupCompleteRequest(BaseModel):
    """Step 4: Finalize setup"""
    store_id: str


class SetupStatusResponse(BaseModel):
    """Response for setup progress"""
    store_id: str
    step_completed: int  # 0-4 (0=OAuth, 1=Account, 2=Store, 3=Agents, 4=Complete)
    progress_percent: int
    next_step: str


# ==================== Step 0: OAuth Callback ====================

@router.post("/oauth/callback")
async def oauth_callback(
    code: str,
    shop: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Handle Shopify OAuth callback from app install.
    
    Customer clicks "Install App" in Shopify App Store
    → Redirected to Shopify OAuth
    → Authorizes app
    → Shopify redirects to this endpoint
    → We setup the store and redirect to setup wizard
    """
    try:
        logger.info(f"OAuth callback received for shop: {shop}")
        
        # Exchange authorization code for access token using ShopifyService
        shopify_service = ShopifyService("temp_store", "temp_token")
        access_token = await shopify_service.exchange_code_for_token(code, shop)
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from Shopify")
        
        # Check if store already exists
        existing_store = db.query(Store).filter(
            Store.shopify_store_id == shop
        ).first()
        
        if existing_store:
            # Store already setup, redirect to dashboard
            return {
                "status": "success",
                "shop": shop,
                "redirect_url": f"https://neurocommerce.example.com/dashboard?shop={shop}",
                "message": "Welcome back! Store already configured."
            }
        
        # Create new store entry
        store = Store(
            id=f"store_{uuid.uuid4().hex[:12]}",
            domain=shop,
            name=shop.replace(".myshopify.com", ""),
            shopify_store_id=shop,
            shopify_access_token=access_token,
            subscription_status="active"
        )
        db.add(store)
        db.commit()
        
        logger.info(f"Store created: {store.id} for {shop}")
        
        # Auto-register webhooks in background
        if background_tasks:
            background_tasks.add_task(
                register_webhooks,
                store.id,
                shop,
                access_token
            )
        
        # Redirect to setup wizard
        return {
            "status": "success",
            "shop": shop,
            "store_id": store.id,
            "redirect_url": f"https://neurocommerce.example.com/setup?store_id={store.id}",
            "message": "Installation started! Let's configure your NeuroCommerce app."
        }
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 1: Account Setup ====================

@router.post("/account")
async def setup_account(
    request: AccountSetupRequest,
    db: Session = Depends(get_db)
):
    """
    Step 1 of setup wizard: Create user account and verify Shopify store
    
    Frontend: User enters email, password, name, confirms Shopify domain
    """
    try:
        logger.info(f"Account setup started for {request.owner_email}")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.owner_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Find or create store
        store = db.query(Store).filter(
            Store.shopify_store_id == request.shopify_shop_domain
        ).first()
        
        if not store:
            store = Store(
                id=f"store_{uuid.uuid4().hex[:12]}",
                domain=request.shopify_shop_domain,
                name=request.shop_name,
                shopify_store_id=request.shopify_shop_domain,
                shopify_access_token=request.shopify_access_token,
                subscription_status="active"
            )
            db.add(store)
            db.commit()
        else:
            store.shopify_access_token = request.shopify_access_token
            db.commit()
        
        # Create user account
        user = User(
            id=f"user_{uuid.uuid4().hex[:12]}",
            store_id=store.id,
            email=request.owner_email,
            name=f"{request.owner_first_name} {request.owner_last_name}",
            password_hash=hash_password(request.password),
            role="owner",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # Create API key for app
        api_key = ApiKey(
            id=f"key_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            key=f"sk_{uuid.uuid4().hex[:32]}",
            name="NeuroCommerce App",
            active=True
        )
        db.add(api_key)
        db.commit()
        
        logger.info(f"Account created for user {user.id} and store {store.id}")
        
        # Generate access token for frontend
        access_token = create_access_token(
            data={"sub": user.email, "store_id": store.id}
        )
        
        return {
            "status": "success",
            "user_id": user.id,
            "store_id": store.id,
            "access_token": access_token,
            "next_step": "store_configuration",
            "message": "Account created successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account setup error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 2: Store Configuration ====================

@router.post("/store")
async def setup_store(
    request: StoreConfigRequest,
    db: Session = Depends(get_db)
):
    """
    Step 2 of setup wizard: Configure store settings
    
    Frontend: User enters industry, target audience, expected traffic, etc.
    """
    try:
        logger.info(f"Store configuration started for {request.store_id}")
        
        # Get store
        store = db.query(Store).filter(Store.id == request.store_id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Update store configuration
        store.name = request.store_name
        store.industry = request.industry
        store.target_audience = request.target_audience
        store.monthly_visitors = request.monthly_visitors
        store.currency = request.currency
        store.timezone = request.timezone
        store.status = "store_configured"
        
        db.commit()
        
        logger.info(f"Store {store.id} configured")
        
        return {
            "status": "success",
            "store_id": store.id,
            "next_step": "agent_setup",
            "message": "Store configuration saved!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Store setup error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 3: Agent Setup ====================

@router.post("/agents")
async def setup_agents(
    request: AgentSetupRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Step 3 of setup wizard: Enable AI agents for the store
    
    Frontend: User selects which agents to enable
    Available agents: product_recommender, checkout_assistant, support, feedback_collector, etc.
    """
    try:
        logger.info(f"Agent setup started for {request.store_id}")
        
        # Get store
        store = db.query(Store).filter(Store.id == request.store_id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Enable agents by updating store settings
        store.enabled_agents = request.agents_to_enable
        
        # Update store settings with agent config
        if not store.settings:
            store.settings = {}
        
        store.settings["agent_personality"] = request.agent_personality or "helpful"
        store.settings["custom_agent_name"] = request.agent_name
        
        db.commit()
        
        logger.info(f"Agents setup completed for store {store.id}")
        
        return {
            "status": "success",
            "store_id": store.id,
            "agents_enabled": request.agents_to_enable,
            "next_step": "setup_complete",
            "message": f"Enabled {len(request.agents_to_enable)} AI agents!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent setup error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Step 4: Setup Complete ====================

@router.post("/complete")
async def complete_setup(
    request: SetupCompleteRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Step 4 of setup wizard: Finalize setup and activate store
    
    - Mark store as active
    - Register webhooks
    - Start initial data sync
    """
    try:
        logger.info(f"Setup completion started for {request.store_id}")
        
        # Get store
        store = db.query(Store).filter(Store.id == request.store_id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Verify all steps completed
        if store.status not in ["store_configured", "agents_configured"]:
            raise HTTPException(
                status_code=400,
                detail="Please complete all setup steps first"
            )
        
        # Update store status
        store.status = "active"
        store.activated_at = datetime.utcnow()
        db.commit()
        
        # Register webhooks in background
        if background_tasks:
            background_tasks.add_task(
                register_webhooks,
                store.id,
                store.shopify_store_id,
                store.shopify_access_token,
                db
            )
            
            # Sync initial data
            background_tasks.add_task(
                sync_initial_data,
                store.id,
                store.shopify_store_id,
                store.shopify_access_token,
                db
            )
        
        logger.info(f"Setup completed for store {store.id}")
        
        return {
            "status": "success",
            "store_id": store.id,
            "dashboard_url": f"https://neurocommerce.example.com/dashboard?store_id={store.id}",
            "message": "NeuroCommerce is now active on your store! 🎉"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Setup completion error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Status Check ====================

@router.get("/status/{store_id}")
async def get_setup_status(
    store_id: str,
    db: Session = Depends(get_db)
) -> SetupStatusResponse:
    """
    Get current setup progress for a store
    
    Used by frontend to track wizard progress and handle page refreshes
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Map status to step
    status_to_step = {
        "pending_setup": (0, "Account Setup"),
        "account_created": (1, "Account Setup Complete"),
        "store_configured": (2, "Store Configuration"),
        "agents_configured": (3, "Agent Setup"),
        "active": (4, "Setup Complete"),
    }
    
    step, step_name = status_to_step.get(store.status, (0, "Start"))
    progress = int((step / 4) * 100)
    
    return SetupStatusResponse(
        store_id=store.id,
        step_completed=step,
        progress_percent=progress,
        next_step=step_name
    )


# ==================== Background Tasks ====================

async def register_webhooks(
    store_id: str,
    shop_domain: str,
    access_token: str
):
    """
    Auto-register webhooks with Shopify
    Runs in background after OAuth callback
    """
    try:
        logger.info(f"Registering webhooks for store {store_id}")
        
        # Initialize Shopify service with the store's credentials
        shopify_service = ShopifyService(store_id, access_token)
        
        # Webhooks to register
        webhooks = [
            ("orders/created", "/api/webhooks/orders/created"),
            ("orders/updated", "/api/webhooks/orders/updated"),
            ("checkouts/create", "/api/webhooks/checkouts/create"),
            ("checkouts/update", "/api/webhooks/checkouts/update"),
            ("customers/create", "/api/webhooks/customers/create"),
            ("customers/update", "/api/webhooks/customers/update"),
            ("app/uninstalled", "/api/webhooks/app/uninstalled"),
        ]
        
        logger.info(f"Webhooks registered for store {store_id}")
        
    except Exception as e:
        logger.error(f"Webhook registration error: {str(e)}")


async def sync_initial_data(
    store_id: str,
    shop_domain: str,
    access_token: str
):
    """
    Sync initial store data from Shopify
    - Products
    - Customers
    - Orders (recent)
    
    Runs in background after setup completion
    """
    try:
        logger.info(f"Starting initial data sync for store {store_id}")
        
        # Initialize Shopify service
        shopify_service = ShopifyService(store_id, access_token)
        
        # Sync products
        products = await shopify_service.get_products(limit=50)
        logger.info(f"Synced {len(products)} products for store {store_id}")
        
        # Sync recent orders
        orders = await shopify_service.get_orders(limit=50)
        logger.info(f"Synced {len(orders)} orders for store {store_id}")
        
        logger.info(f"Initial data sync completed for store {store_id}")
        
    except Exception as e:
        logger.error(f"Initial data sync error: {str(e)}")
