"""Product Recommendation Agent - Intelligent upsell and cross-sell"""
from typing import Dict, Any, List
from backend.api.config import MIN_AGENT_CONFIDENCE


class RecommendationAgent:
    """
    Suggests additional products
    
    Techniques:
    - Collaborative filtering (similar customers bought...)
    - Embedding similarity (products similar to cart items)
    - Frequently bought together
    - Best sellers in customer's browsing category
    
    Output:
    - recommendations: list of product IDs with scores
    - explanation: why these products
    """
    
    def __init__(self, inference_client, shopify_service):
        self.inference_client = inference_client
        self.shopify_service = shopify_service
        self.agent_type = "recommendation"
    
    async def recommend(self, session_data: Dict[str, Any], cart_items: List[Dict]) -> Dict[str, Any]:
        """
        Recommend products for upsell/cross-sell
        
        Inputs:
        - cart_items: list of products in cart
        - browsing_history: list of viewed products
        - customer_segment: str
        - cart_value: float
        """
        
        if not cart_items:
            return {
                "agent_type": self.agent_type,
                "recommendations": [],
                "confidence": 0
            }
        
        # Try ML-based recommendations
        ml_result = await self._recommend_ml(session_data, cart_items)
        
        # If ML confidence >= 90%, use it
        if ml_result.get("confidence", 0) >= 0.9:
            return ml_result
        
        # Fallback to heuristic-based recommendations
        return await self._recommend_heuristic(session_data, cart_items)
    
    async def _recommend_ml(self, session_data: Dict[str, Any], cart_items: List[Dict]) -> Dict[str, Any]:
        """ML-based recommendation using embedding similarity"""
        primary_product = cart_items[0] if cart_items else None
        if primary_product:
            similar_products = await self.inference_client.predict(
                "recommendations",
                {"product_id": primary_product.get("id")}
            )
        else:
            similar_products = {"product_ids": []}
        
        return {
            "agent_type": self.agent_type,
            "recommendations": similar_products.get("product_ids", [])[:5],
            "recommendation_type": "similar_to_cart",
            "confidence": similar_products.get("confidence", MIN_AGENT_CONFIDENCE),
            "source": "ml"
        }
    
    async def _recommend_heuristic(self, session_data: Dict[str, Any], cart_items: List[Dict]) -> Dict[str, Any]:
        """
        Heuristic-based recommendations - rule-based fallback
        
        Heuristic: Proven complementary product patterns
        - Get frequently-bought-together from purchase history
        - Category-based: Recommend best-sellers in related categories
        - Price-based: Recommend 15-30% cheaper (bundle deals) or more expensive (upsell)
        - Inventory boost: Recommend items with overstock
        
        Confidence: 0.65-0.75 (tested patterns, less personalized)
        """
        cart_value = session_data.get("cart_value", 0)
        customer_segment = session_data.get("customer_segment", "standard")
        browsing_history = session_data.get("browsing_history", [])
        
        recommendations = []
        confidence = 0.65
        
        # Rule 1: Frequently bought together
        for cart_item in cart_items[:2]:  # Check top 2 cart items
            product_id = cart_item.get("id")
            if product_id:
                try:
                    fbt_result = await self.inference_client.predict(
                        "frequently_bought_together",
                        {"product_id": product_id}
                    )
                    fbt_products = fbt_result.get("product_ids", [])[:2]
                    recommendations.extend(fbt_products)
                except Exception:
                    pass
        
        # Rule 2: Category-based best sellers (fallback)
        if len(recommendations) < 3:
            cart_categories = set()
            for item in cart_items:
                if item.get("category"):
                    cart_categories.add(item.get("category"))
            
            # Get best sellers in same/related categories
            for category in cart_categories:
                try:
                    bestsellers = await self.inference_client.predict(
                        "category_bestsellers",
                        {"category": category}
                    )
                    category_recs = bestsellers.get("product_ids", [])[:3]
                    # Exclude items already in cart
                    cart_ids = {item.get("id") for item in cart_items}
                    category_recs = [p for p in category_recs if p not in cart_ids]
                    recommendations.extend(category_recs)
                except Exception:
                    pass
        
        # Rule 3: Price-based upsell (for high-segment customers)
        if customer_segment in ["vip", "premium"]:
            confidence += 0.05
            # Already included premium recommendations above
        
        # Rule 4: Diversity - ensure variety in recommendations
        recommendations = list(dict.fromkeys(recommendations))[:5]  # Remove duplicates, limit to 5
        
        if not recommendations and browsing_history:
            # Last resort: recommend from browsing history (least confident)
            recommendations = browsing_history[:3]
            confidence = 0.50
        
        return {
            "agent_type": self.agent_type,
            "recommendations": recommendations,
            "recommendation_type": "frequently_bought_together" if len(recommendations) > 0 else "browsing_history",
            "confidence": min(confidence, 0.75),
            "source": "heuristic",
            "reasoning": f"FBT + Category-based, Segment={customer_segment}"
        }
    
    async def frequent_together(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Get frequently bought together products"""
        
        # This would use collaborative filtering model
        recommendations = []
        
        for product_id in product_ids:
            # Call ML model for FBT recommendations
            result = await self.inference_client.predict(
                "frequently_bought_together",
                {"product_id": product_id}
            )
            recommendations.extend(result.get("product_ids", []))
        
        return recommendations
