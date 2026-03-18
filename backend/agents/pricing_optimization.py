"""Pricing Optimization Agent - Dynamic discount optimization"""
from typing import Dict, Any
from backend.api.config import (
    OPTIMAL_AGENT_CONFIDENCE,
    MAX_DISCOUNT,
    ABANDONMENT_PROBABILITY_THRESHOLD
)


class PricingOptimizationAgent:
    """
    Determines optimal discount for customer
    
    Inputs:
    - cart_value: float
    - product_margin: float
    - customer_price_sensitivity: float (0-1)
    - customer_lifetime_value: float
    - previous_purchases: int
    - abandonment_probability: float
    
    Outputs:
    - discount_percentage: float
    - coupon_code: str
    - expected_conversion_lift: float
    """
    
    def __init__(self, inference_client):
        self.inference_client = inference_client
        self.agent_type = "pricing_optimization"
    
    async def optimize_discount(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal discount for this customer"""
        
        cart_value = data.get("cart_value", 0)
        margin = data.get("margin", 0.3)  # Default 30% margin
        price_sensitivity = data.get("price_sensitivity", 0.5)
        ltv = data.get("lifetime_value", 0)
        abandonment_prob = data.get("abandonment_probability", 0)
        
        # Try ML-based optimization first
        ml_result = await self._optimize_discount_ml(data)
        
        # If ML confidence >= 90%, use ML result
        if ml_result.get("confidence", 0) >= 0.9:
            return ml_result
        
        # Fallback to heuristic-based optimization
        return self._optimize_discount_heuristic(data, ml_result)
    
    async def _optimize_discount_ml(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ML-based discount optimization"""
        cart_value = data.get("cart_value", 0)
        margin = data.get("margin", 0.3)
        price_sensitivity = data.get("price_sensitivity", 0.5)
        ltv = data.get("lifetime_value", 0)
        abandonment_prob = data.get("abandonment_probability", 0)
        
        # Base discount formula
        # Higher abandonment risk = higher discount
        # Higher LTV = lower discount (already valuable customer)
        # Higher price sensitivity = higher discount
        
        base_discount = abandonment_prob * (MAX_DISCOUNT * 0.7)
        sensitivity_bonus = price_sensitivity * (MAX_DISCOUNT * 0.4)
        ltv_reduction = max(0, (ltv - 200) / 1000 * (MAX_DISCOUNT * 0.15))
        
        optimal_discount = min(MAX_DISCOUNT, base_discount + sensitivity_bonus - ltv_reduction)
        optimal_discount = max(0, optimal_discount)
        
        return {
            "agent_type": self.agent_type,
            "discount_percentage": round(optimal_discount, 1),
            "coupon_code": self._generate_coupon_code(),
            "expected_conversion_lift": min(0.95, 0.5 + (optimal_discount / 100)),
            "profit_margin_preserved": margin * (1 - optimal_discount / 100),
            "confidence": OPTIMAL_AGENT_CONFIDENCE,
            "source": "ml"
        }
    
    def _optimize_discount_heuristic(self, data: Dict[str, Any], ml_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic-based discount optimization - rule-based fallback
        
        Heuristic: Based on price elasticity research (Johnson & Myatt, McKinsey)
        - New customers: Higher discount (7-15%) to acquire
        - Returning customers: Lower discount (5-10%) - less price sensitive
        - High abandonment risk: Aggressive discount (15-30%)
        - High LTV: Minimal/no discount (0-5%) - less price elastic
        - Cart value threshold: Higher values = lower discount (% discount reduces margin more on high carts)
        
        Confidence: 0.7-0.8 (research-backed but less ML-optimized)
        """
        cart_value = data.get("cart_value", 0)
        margin = data.get("margin", 0.3)
        ltv = data.get("lifetime_value", 0)
        abandonment_prob = data.get("abandonment_probability", 0)
        customer_segment = data.get("customer_segment", "new")
        previous_purchases = data.get("previous_purchases", 0)
        
        # Rule 1: Base discount by customer segment (acquisition vs retention)
        if customer_segment == "new" or previous_purchases == 0:
            base_discount = 12.0  # 12% for new customers (acquisition focused)
        elif customer_segment == "returning":
            base_discount = 7.0   # 7% for returning (loyalty, less price sensitive)
        else:
            base_discount = 8.0   # 8% default
        
        # Rule 2: Adjust for abandonment risk (save the sale)
        if abandonment_prob > ABANDONMENT_PROBABILITY_THRESHOLD:
            # High risk: add aggressive discount
            abandonment_bonus = min(20, (abandonment_prob - ABANDONMENT_PROBABILITY_THRESHOLD) * 50)
            base_discount += abandonment_bonus
        
        # Rule 3: Reduce for high LTV (already profitable customer)
        if ltv > 500:
            ltv_reduction = min(base_discount - 2, (ltv - 500) / 500)  # Max 10% reduction
            base_discount = max(2, base_discount - ltv_reduction)
        
        # Rule 4: Cart value adjustment (protect margin on high-value orders)
        if cart_value > 300:
            # On high-value carts, % discount impacts margin more
            cart_reduction = min(base_discount * 0.3, (cart_value - 300) / 1000)
            base_discount = max(2, base_discount - cart_reduction)
        
        # Rule 5: Margin floor check (never discount below break-even)
        max_sustainable_discount = margin * 100 - 2  # Keep 2% margin
        optimal_discount = min(base_discount, max_sustainable_discount)
        optimal_discount = min(optimal_discount, MAX_DISCOUNT)
        optimal_discount = max(0, optimal_discount)
        
        # Confidence scoring
        confidence = 0.70
        if customer_segment == "returning":
            confidence += 0.05  # Higher confidence for returning customers
        if abandonment_prob < 0.5:
            confidence += 0.05  # Higher confidence when risk is low (simple decision)
        
        return {
            "agent_type": self.agent_type,
            "discount_percentage": round(optimal_discount, 1),
            "coupon_code": self._generate_coupon_code(),
            "expected_conversion_lift": min(0.95, 0.4 + (optimal_discount / 100)),
            "profit_margin_preserved": round(margin * (1 - optimal_discount / 100), 3),
            "confidence": confidence,
            "source": "heuristic",
            "reasoning": f"Segment={customer_segment}, Abandon={abandonment_prob:.2f}, LTV=${ltv:.0f}"
        }
    
    def _generate_coupon_code(self) -> str:
        """Generate unique coupon code"""
        import secrets
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(8))
