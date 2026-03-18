#!/usr/bin/env python3
"""
Simulate Shopify webhook deliveries for testing
"""

import requests
import json
import hmac
import hashlib
import base64
from datetime import datetime

NEURO_API = "http://localhost:8000"
SHOPIFY_SECRET = "test_api_secret_67890"  # Would be from Shopify


def create_webhook_signature(body: str) -> str:
    """
    Create HMAC signature like Shopify does
    """
    secret = SHOPIFY_SECRET.encode()
    message = body.encode()
    
    hash_obj = hmac.new(secret, message, hashlib.sha256)
    signature = base64.b64encode(hash_obj.digest()).decode()
    
    return signature


def send_webhook(topic: str, payload: dict):
    """
    Send webhook to our backend
    """
    print(f"\n📨 Sending {topic} webhook")
    print("-" * 40)
    
    body = json.dumps(payload)
    signature = create_webhook_signature(body)
    
    url = f"{NEURO_API}/api/webhooks/{topic.replace('/', '_')}"
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Hmac-SHA256": signature,
        "X-Shopify-Shop-Api-Call-Limit": "1/40"
    }
    
    print(f"URL: POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)[:200]}...")
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Response: {response.status_code}")
    
    return response.status_code == 200


def test_orders_created():
    """Simulate orders/created webhook"""
    payload = {
        "id": 123456789,
        "order_number": 1001,
        "email": "customer@example.com",
        "total_price": "99.99",
        "subtotal_price": "89.99",
        "total_tax": "10.00",
        "currency": "USD",
        "financial_status": "paid",
        "fulfillment_status": "fulfilled",
        "confirmed": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "shop": {
            "id": 1,
            "myshopify_domain": "test-store.myshopify.com"
        },
        "customer": {
            "id": 987654321,
            "email": "customer@example.com",
            "first_name": "John",
            "last_name": "Doe"
        },
        "line_items": [
            {
                "id": 1,
                "title": "Test Product",
                "quantity": 1,
                "price": "99.99"
            }
        ]
    }
    
    return send_webhook("orders/created", payload)


def test_checkouts_create():
    """Simulate checkouts/create webhook"""
    payload = {
        "token": "checkout_token_123",
        "total_price": "99.99",
        "subtotal_price": "89.99",
        "total_tax": "10.00",
        "total_line_items_price": "99.99",
        "currency": "USD",
        "email": "customer@example.com",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "shop": {
            "myshopify_domain": "test-store.myshopify.com"
        },
        "line_items": [
            {
                "id": 1,
                "title": "Test Product",
                "quantity": 1,
                "price": "99.99"
            }
        ]
    }
    
    return send_webhook("checkouts/create", payload)


def test_customers_create():
    """Simulate customers/create webhook"""
    payload = {
        "id": 987654321,
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "555-1234",
        "orders_count": 1,
        "total_spent": "99.99",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "verified_email": True,
        "addresses": [
            {
                "address1": "123 Test St",
                "city": "Test City",
                "province": "NY",
                "country": "US",
                "zip": "10001",
                "default": True
            }
        ]
    }
    
    return send_webhook("customers/create", payload)


def run_all_webhooks():
    """Test all webhook types"""
    print("""
    🔗 WEBHOOK SIMULATION
    ====================
    
    Testing webhook delivery to backend
    """)
    
    results = {
        "orders/created": test_orders_created(),
        "checkouts/create": test_checkouts_create(),
        "customers/create": test_customers_create()
    }
    
    print("\n" + "=" * 40)
    print("RESULTS:")
    print("=" * 40)
    
    for webhook, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{webhook}: {status}")
    
    print("\nCheck database for events:")
    print("make db-shell")
    print("SELECT * FROM events LIMIT 10;")


if __name__ == "__main__":
    run_all_webhooks()
