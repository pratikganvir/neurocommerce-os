#!/usr/bin/env python3
"""
Mock Shopify Server for Local Testing

Simulates Shopify OAuth, API responses, and webhook delivery
No real Shopify credentials needed!
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Initialize mock server
app = FastAPI(title="Mock Shopify Server", version="1.0")

# Mock data store (in-memory, resets on restart)
MOCK_STATE = {
    "authorization_codes": {},  # code -> {shop, timestamp, scopes}
    "access_tokens": {},  # token -> {shop, expires_at, scopes}
    "stores": {},  # shop -> {products, orders, customers}
    "webhooks": {},  # shop -> [webhooks]
}

# Constants
MOCK_API_KEY = "test_api_key_12345"
MOCK_API_SECRET = "test_api_secret_67890"
SHOPIFY_API_VERSION = "2024-01"


# ==================== OAuth Endpoints ====================

@app.get("/admin/oauth/authorize")
async def oauth_authorize(
    client_id: str,
    scope: str,
    redirect_uri: str,
    state: str,
    shop: str
):
    """
    Simulate Shopify OAuth authorization screen
    In real flow: User sees approval screen and clicks "Authorize"
    For testing: Auto-approve and redirect
    """
    
    if client_id != MOCK_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Generate authorization code
    code = f"auth_code_{secrets.token_hex(16)}"
    
    # Store for later token exchange
    MOCK_STATE["authorization_codes"][code] = {
        "shop": shop,
        "scopes": scope.split(","),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }
    
    # In real flow: Browser redirects to redirect_uri
    # For testing: Return redirect URL for inspection
    callback_url = f"{redirect_uri}?code={code}&shop={shop}&state={state}"
    
    return JSONResponse({
        "redirect_url": callback_url,
        "message": "[MOCK] Shopify would redirect to this URL"
    })


@app.post("/admin/oauth/access_token")
async def oauth_token_exchange(request: Request):
    """
    Exchange authorization code for access token
    This is called by our backend
    """
    
    body = await request.json()
    code = body.get("code")
    shop = body.get("shop")
    client_id = body.get("client_id")
    client_secret = body.get("client_secret")
    
    # Validate credentials
    if client_id != MOCK_API_KEY or client_secret != MOCK_API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Validate authorization code
    if code not in MOCK_STATE["authorization_codes"]:
        raise HTTPException(status_code=401, detail="Invalid or expired code")
    
    auth_data = MOCK_STATE["authorization_codes"][code]
    
    # Check code not expired
    expires_at = datetime.fromisoformat(auth_data["expires_at"])
    if datetime.utcnow() > expires_at:
        del MOCK_STATE["authorization_codes"][code]
        raise HTTPException(status_code=401, detail="Code expired")
    
    # Generate access token
    access_token = f"shpat_{secrets.token_hex(32)}"
    
    # Store token
    MOCK_STATE["access_tokens"][access_token] = {
        "shop": shop,
        "scopes": auth_data["scopes"],
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
    }
    
    # Clean up authorization code
    del MOCK_STATE["authorization_codes"][code]
    
    return JSONResponse({
        "access_token": access_token,
        "scope": ",".join(auth_data["scopes"])
    })


# ==================== Admin API Endpoints ====================

@app.get("/admin/api/{version}/shop.json")
async def get_shop(version: str, request: Request):
    """Get shop information"""
    
    token = request.headers.get("X-Shopify-Access-Token")
    if token not in MOCK_STATE["access_tokens"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    shop_domain = MOCK_STATE["access_tokens"][token]["shop"]
    
    return JSONResponse({
        "shop": {
            "id": f"gid://shopify/Shop/123456789",
            "name": f"Test Store {shop_domain}",
            "email": f"owner@{shop_domain}",
            "customer_email": f"customer@{shop_domain}",
            "domain": shop_domain,
            "province": "NY",
            "country": "US",
            "country_code": "US",
            "province_code": "NY",
            "timezone": "America/New_York",
            "iana_timezone": "America/New_York",
            "currency": "USD",
            "primary_locale": "en-US",
            "plan_name": "basic",
            "shop_owner": "Test Owner",
            "has_inventory_tracking": True,
            "has_online_store": True,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-03-15T10:00:00Z"
        }
    })


@app.get("/admin/api/{version}/products.json")
async def get_products(version: str, request: Request, limit: int = 50):
    """Get products"""
    
    token = request.headers.get("X-Shopify-Access-Token")
    if token not in MOCK_STATE["access_tokens"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Generate mock products
    products = []
    for i in range(min(limit, 5)):  # Return up to 5 mock products
        products.append({
            "id": f"gid://shopify/Product/{1000 + i}",
            "title": f"Test Product {i+1}",
            "handle": f"test-product-{i+1}",
            "vendor": "Test Vendor",
            "product_type": "Test Type",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-03-15T10:00:00Z",
            "published_at": "2026-01-01T00:00:00Z",
            "tags": ["test", "mock"],
            "status": "active",
            "variants": [
                {
                    "id": f"gid://shopify/ProductVariant/{2000 + i}",
                    "title": "Default Title",
                    "price": "99.99",
                    "sku": f"TEST-{i+1}",
                    "available": True,
                    "inventory_quantity": 100
                }
            ]
        })
    
    return JSONResponse({"products": products})


@app.get("/admin/api/{version}/customers.json")
async def get_customers(version: str, request: Request, limit: int = 50):
    """Get customers"""
    
    token = request.headers.get("X-Shopify-Access-Token")
    if token not in MOCK_STATE["access_tokens"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Generate mock customers
    customers = []
    for i in range(min(limit, 3)):  # Return up to 3 mock customers
        customers.append({
            "id": f"gid://shopify/Customer/{3000 + i}",
            "email": f"customer{i+1}@example.com",
            "first_name": f"Customer{i+1}",
            "last_name": "Test",
            "phone": "555-1234",
            "orders_count": i + 1,
            "total_spent": str((i + 1) * 100),
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-03-15T10:00:00Z",
            "verified_email": True,
            "addresses": [
                {
                    "address1": "123 Test St",
                    "address2": "",
                    "city": "Test City",
                    "province": "NY",
                    "country": "US",
                    "zip": "10001",
                    "phone": "555-1234",
                    "name": f"Customer{i+1} Test",
                    "default": True
                }
            ]
        })
    
    return JSONResponse({"customers": customers})


@app.get("/admin/api/{version}/orders.json")
async def get_orders(version: str, request: Request, limit: int = 50, status: str = "any"):
    """Get orders"""
    
    token = request.headers.get("X-Shopify-Access-Token")
    if token not in MOCK_STATE["access_tokens"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Generate mock orders
    orders = []
    for i in range(min(limit, 5)):  # Return up to 5 mock orders
        orders.append({
            "id": f"gid://shopify/Order/{4000 + i}",
            "order_number": 1000 + i,
            "email": f"customer{i}@example.com",
            "total_price": f"{99.99 * (i+1)}",
            "subtotal_price": f"{89.99 * (i+1)}",
            "total_tax": f"{10 * (i+1)}",
            "currency": "USD",
            "financial_status": "paid",
            "fulfillment_status": "fulfilled",
            "confirmed": True,
            "created_at": "2026-03-01T00:00:00Z",
            "updated_at": "2026-03-15T10:00:00Z",
            "customer": {
                "id": f"gid://shopify/Customer/{3000 + i}",
                "email": f"customer{i}@example.com",
                "first_name": f"Customer{i}",
                "last_name": "Test"
            },
            "line_items": [
                {
                    "id": f"gid://shopify/LineItem/{5000 + i}",
                    "title": f"Test Product {i}",
                    "quantity": 1,
                    "price": f"{99.99 * (i+1)}"
                }
            ]
        })
    
    return JSONResponse({"orders": orders})


# ==================== Webhook Management ====================

@app.post("/admin/api/{version}/webhook_subscriptions.json")
async def create_webhook(version: str, request: Request):
    """Create webhook subscription"""
    
    token = request.headers.get("X-Shopify-Access-Token")
    if token not in MOCK_STATE["access_tokens"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    body = await request.json()
    webhook = body.get("webhook_subscription", {})
    
    shop_domain = MOCK_STATE["access_tokens"][token]["shop"]
    
    # Store webhook
    if shop_domain not in MOCK_STATE["webhooks"]:
        MOCK_STATE["webhooks"][shop_domain] = []
    
    registered_webhook = {
        "id": f"gid://shopify/WebhookSubscription/{secrets.randbelow(1000000)}",
        "topic": webhook.get("topic"),
        "callback_url": webhook.get("callback_url"),
        "format": webhook.get("format", "json"),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    MOCK_STATE["webhooks"][shop_domain].append(registered_webhook)
    
    return JSONResponse({
        "webhook_subscription": registered_webhook
    }, status_code=201)


@app.get("/admin/api/{version}/webhook_subscriptions.json")
async def list_webhooks(version: str, request: Request):
    """List registered webhooks"""
    
    token = request.headers.get("X-Shopify-Access-Token")
    if token not in MOCK_STATE["access_tokens"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    shop_domain = MOCK_STATE["access_tokens"][token]["shop"]
    
    webhooks = MOCK_STATE["webhooks"].get(shop_domain, [])
    
    return JSONResponse({
        "webhook_subscriptions": webhooks
    })


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "ok",
        "message": "Mock Shopify Server Running"
    })


# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup():
    print("""
    🎭 Mock Shopify Server Starting
    
    This server simulates Shopify for local testing.
    No real Shopify credentials needed!
    
    Available endpoints:
    - /admin/oauth/authorize
    - /admin/oauth/access_token
    - /admin/api/2024-01/shop.json
    - /admin/api/2024-01/products.json
    - /admin/api/2024-01/customers.json
    - /admin/api/2024-01/orders.json
    - /admin/api/2024-01/webhook_subscriptions.json
    
    Test credentials:
    - API Key: test_api_key_12345
    - API Secret: test_api_secret_67890
    """)


if __name__ == "__main__":
    print("Starting Mock Shopify Server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
