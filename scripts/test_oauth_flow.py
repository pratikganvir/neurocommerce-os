#!/usr/bin/env python3
"""
Simulate complete OAuth flow for testing
"""

import requests
import json
from urllib.parse import urlencode, parse_qs, urlparse

# Configuration
MOCK_SHOPIFY_SERVER = "http://localhost:8001"  # Mock server
NEURO_API = "http://localhost:8000"  # Our backend
FRONTEND = "http://localhost:3000"  # Our frontend

# Test credentials
SHOP = "test-store.myshopify.com"
API_KEY = "test_api_key_12345"
API_SECRET = "test_api_secret_67890"
SCOPES = "write_products,read_products,write_orders,read_orders,write_webhooks,read_webhooks"
REDIRECT_URI = f"{NEURO_API}/api/setup/oauth/callback"


def step1_request_authorization():
    """
    Step 1: Request authorization from Shopify
    In real flow: User clicks "Install App" button
    """
    print("\n📌 Step 1: Request Authorization")
    print("=" * 50)
    
    params = {
        "client_id": API_KEY,
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": "random_state_12345"
    }
    
    url = f"{MOCK_SHOPIFY_SERVER}/admin/oauth/authorize?{urlencode(params)}&shop={SHOP}"
    
    print(f"Authorization URL: {url}\n")
    
    # Mock: Get authorization code
    response = requests.get(url)
    data = response.json()
    
    redirect_url = data["redirect_url"]
    print(f"Shopify would redirect to: {redirect_url}\n")
    
    # Extract code and state
    parsed_url = urlparse(redirect_url)
    params = parse_qs(parsed_url.query)
    code = params["code"][0]
    shop = params["shop"][0]
    
    print(f"✓ Authorization code received: {code}")
    print(f"✓ Shop: {shop}")
    
    return code, shop


def step2_exchange_code_for_token(code, shop):
    """
    Step 2: Exchange authorization code for access token
    Backend calls Shopify (or mock) to get access token
    """
    print("\n📌 Step 2: Exchange Code for Token")
    print("=" * 50)
    
    print(f"Exchanging code: {code}")
    
    payload = {
        "client_id": API_KEY,
        "client_secret": API_SECRET,
        "code": code
    }
    
    url = f"{MOCK_SHOPIFY_SERVER}/admin/oauth/access_token"
    response = requests.post(url, json=payload)
    
    data = response.json()
    access_token = data["access_token"]
    scope = data["scope"]
    
    print(f"✓ Access token received: {access_token}")
    print(f"✓ Scopes: {scope}")
    
    return access_token


def step3_call_oauth_callback(code, shop):
    """
    Step 3: Backend receives OAuth callback and creates store
    """
    print("\n📌 Step 3: OAuth Callback (Our Backend)")
    print("=" * 50)
    
    payload = {
        "code": code,
        "shop": shop
    }
    
    url = f"{NEURO_API}/api/setup/oauth/callback"
    
    print(f"Calling: POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    store_id = data["store_id"]
    redirect_url = data["redirect_url"]
    
    print(f"✓ Store created: {store_id}")
    print(f"✓ Redirect URL: {redirect_url}")
    
    return store_id


def step4_setup_wizard(store_id):
    """
    Step 4: Customer redirected to setup wizard
    """
    print("\n📌 Step 4: Setup Wizard")
    print("=" * 50)
    
    url = f"{FRONTEND}/setup?store_id={store_id}"
    print(f"Setup wizard would load at: {url}")
    print("Customer fills out 4 steps...")
    print("✓ Account Setup")
    print("✓ Store Configuration")
    print("✓ Agent Setup")
    print("✓ Completion")


def run_complete_flow():
    """Run complete OAuth flow"""
    print("""
    🎭 SIMULATING COMPLETE OAUTH FLOW
    ================================
    
    This simulates what happens when customer installs app:
    1. Customer clicks "Install App" in Shopify App Store
    2. Shopify OAuth consent screen
    3. Customer authorizes
    4. Shopify redirects with authorization code
    5. Our backend exchanges code for access token
    6. Our backend creates store
    7. Customer redirected to setup wizard
    """)
    
    try:
        # Step 1: Request authorization
        code, shop = step1_request_authorization()
        
        # Step 2: Exchange code for token (demonstrated but not used directly)
        access_token = step2_exchange_code_for_token(code, shop)
        
        # Step 3: OAuth callback to our backend
        store_id = step3_call_oauth_callback(code, shop)
        
        if store_id:
            # Step 4: Setup wizard
            step4_setup_wizard(store_id)
            
            print("\n" + "=" * 50)
            print("✅ OAUTH FLOW SIMULATION COMPLETE!")
            print("=" * 50)
            print(f"\nNext steps:")
            print(f"1. Open setup wizard: {FRONTEND}/setup?store_id={store_id}")
            print(f"2. Fill out account and store info")
            print(f"3. Enable AI agents")
            print(f"4. Click 'Activate'")
            print(f"\nThe app will be live on the store! 🚀")
        
    except Exception as e:
        print(f"\n❌ Error during OAuth flow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_complete_flow()
