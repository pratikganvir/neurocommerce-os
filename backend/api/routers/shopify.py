"""Shopify integration routes"""
import hmac
import hashlib
import base64
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ...models.models import Store, Cart, Customer, Order
from ...services.shopify_service import ShopifyService
from ...services.kafka_producer import produce_event

router = APIRouter()


@router.post("/webhooks/checkout/create")
async def shopify_checkout_create(request: Request, db: Session = Depends(get_db)):
    """Handle Shopify checkout.created webhook"""
    body = await request.body()
    
    # Verify HMAC signature
    if not _verify_shopify_webhook(body, request.headers.get("X-Shopify-Hmac-SHA256")):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(body)
    
    # Find store by shopify ID (from headers)
    store = db.query(Store).filter(
        Store.shopify_store_id == data.get("shop", {}).get("myshopify_domain")
    ).first()
    
    if not store:
        return {"status": "ok"}  # Store not integrated
    
    # Create/update cart
    cart = Cart(
        id=f"cart_{data['token']}",
        store_id=store.id,
        shopify_cart_token=data['token'],
        cart_value=float(data.get('total_price', 0)),
        item_count=len(data.get('line_items', [])),
        items=data.get('line_items', []),
        status="active"
    )
    db.add(cart)
    db.commit()
    
    # Publish event
    produce_event({
        "event_type": "checkout_created",
        "store_id": store.id,
        "checkout_token": data['token'],
        "cart_value": cart.cart_value,
        "timestamp": data.get('created_at', '')
    })
    
    return {"status": "ok"}


@router.post("/webhooks/checkout/update")
async def shopify_checkout_update(request: Request, db: Session = Depends(get_db)):
    """Handle Shopify checkout.updated webhook"""
    body = await request.body()
    
    # Verify HMAC
    if not _verify_shopify_webhook(body, request.headers.get("X-Shopify-Hmac-SHA256")):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(body)
    
    # Update cart
    cart = db.query(Cart).filter(Cart.shopify_cart_token == data['token']).first()
    if cart:
        cart.cart_value = float(data.get('total_price', 0))
        cart.item_count = len(data.get('line_items', []))
        cart.items = data.get('line_items', [])
        cart.updated_at = datetime.utcnow()
        db.commit()
    
    return {"status": "ok"}


@router.post("/webhooks/orders/create")
async def shopify_order_create(request: Request, db: Session = Depends(get_db)):
    """Handle Shopify orders.created webhook"""
    body = await request.body()
    
    if not _verify_shopify_webhook(body, request.headers.get("X-Shopify-Hmac-SHA256")):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(body)
    
    # Find store
    store = db.query(Store).filter(
        Store.shopify_store_id == data.get("shop", {}).get("myshopify_domain")
    ).first()
    
    if not store:
        return {"status": "ok"}
    
    # Update/create customer
    customer = db.query(Customer).filter(
        Customer.shopify_customer_id == data['customer']['id']
    ).first()
    
    if not customer:
        customer = Customer(
            id=f"cust_{data['customer']['id']}",
            store_id=store.id,
            shopify_customer_id=str(data['customer']['id']),
            email=data['customer'].get('email', ''),
            first_name=data['customer'].get('first_name', ''),
            last_name=data['customer'].get('last_name', '')
        )
        db.add(customer)
    
    # Update customer metrics
    customer.total_orders = (customer.total_orders or 0) + 1
    customer.last_order_date = datetime.utcnow()
    customer.lifetime_value = (customer.lifetime_value or 0) + float(data.get('total_price', 0))
    
    db.commit()
    
    # Publish event
    produce_event({
        "event_type": "order_created",
        "store_id": store.id,
        "customer_id": customer.id,
        "order_id": data['id'],
        "order_value": float(data.get('total_price', 0)),
        "timestamp": data.get('created_at', '')
    })
    
    return {"status": "ok"}


@router.post("/oauth/callback")
async def shopify_oauth_callback(code: str, shop: str, db: Session = Depends(get_db)):
    """Handle Shopify OAuth callback"""
    shopify_service = ShopifyService(db)
    
    # Exchange code for access token
    access_token = await shopify_service.exchange_code_for_token(code, shop)
    
    if not access_token:
        raise HTTPException(status_code=400, detail="OAuth failed")
    
    # Update store
    store = db.query(Store).filter(Store.shopify_store_id == shop).first()
    if store:
        store.shopify_access_token = access_token
        db.commit()
    
    return {"status": "success", "shop": shop}


def _verify_shopify_webhook(body: bytes, hmac_header: str) -> bool:
    """Verify Shopify webhook HMAC signature"""
    if not hmac_header:
        return False
    
    import os
    secret = os.getenv("SHOPIFY_API_SECRET", "").encode()
    
    hash_object = hmac.new(secret, body, hashlib.sha256)
    computed_hmac = base64.b64encode(hash_object.digest()).decode()
    
    return hmac.compare_digest(computed_hmac, hmac_header)
