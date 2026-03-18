"""Shopify API integration service"""
import os
import aiohttp
import json
from typing import Optional, Dict, Any

SHOPIFY_API_VERSION = "2024-01"


class ShopifyService:
    """Service for Shopify API interactions"""
    
    def __init__(self, store_id: str, access_token: str):
        self.store_id = store_id
        self.access_token = access_token
    
    async def exchange_code_for_token(self, code: str, shop: str) -> Optional[str]:
        """Exchange OAuth code for access token"""
        api_key = os.getenv("SHOPIFY_API_KEY")
        api_secret = os.getenv("SHOPIFY_API_SECRET")
        
        url = f"https://{shop}/admin/oauth/access_token"
        
        data = {
            "client_id": api_key,
            "client_secret": api_secret,
            "code": code
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("access_token")
        except Exception as e:
            print(f"OAuth exchange failed: {e}")
        
        return None
    
    async def get_orders(self, limit: int = 50, status: str = "any") -> list:
        """Get orders from Shopify"""
        url = f"https://{self.shop}/admin/api/{SHOPIFY_API_VERSION}/orders.json"
        
        params = {
            "limit": limit,
            "status": status,
            "fields": "id,email,total_price,line_items,created_at"
        }
        
        headers = {
            "X-Shopify-Access-Token": self.access_token
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("orders", [])
        except Exception as e:
            print(f"Failed to fetch orders: {e}")
        
        return []
    
    async def create_discount(self, code: str, discount_type: str, value: float) -> Optional[str]:
        """Create a discount code"""
        url = f"https://{self.shop}/admin/api/{SHOPIFY_API_VERSION}/discount_codes.json"
        
        payload = {
            "discount_code": {
                "price_rule": {
                    "title": f"Discount {code}",
                    "target_type": "line_item",
                    "target_selection": "all",
                    "allocation_method": "across",
                    "value": f"-{value}",
                    "value_type": "percentage" if discount_type == "percentage" else "fixed_amount",
                    "customer_selection": "all"
                },
                "code": code
            }
        }
        
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return data.get("discount_code", {}).get("code")
        except Exception as e:
            print(f"Failed to create discount: {e}")
        
        return None
    
    async def get_products(self, limit: int = 50) -> list:
        """Get products from Shopify"""
        url = f"https://{self.shop}/admin/api/{SHOPIFY_API_VERSION}/products.json"
        
        params = {
            "limit": limit,
            "fields": "id,title,handle,image,vendor,product_type"
        }
        
        headers = {
            "X-Shopify-Access-Token": self.access_token
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("products", [])
        except Exception as e:
            print(f"Failed to fetch products: {e}")
        
        return []
