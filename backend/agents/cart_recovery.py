"""Cart Recovery Agent - Multi-channel cart abandonment recovery"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from backend.api.config import OPTIMAL_AGENT_CONFIDENCE


class CartRecoveryAgent:
    """
    Triggers after cart abandonment
    
    Channels:
    - email (primary)
    - SMS (secondary)
    - WhatsApp (for opted-in customers)
    - push (if app installed)
    
    Strategy:
    - 1 hour: Product email reminder
    - 24 hours: Personal message with incentive
    - 72 hours: Last chance message
    """
    
    def __init__(self, messaging_service, inference_client):
        self.messaging_service = messaging_service
        self.inference_client = inference_client
        self.agent_type = "cart_recovery"
    
    async def plan_recovery(self, cart_data: Dict[str, Any], customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan recovery campaign for abandoned cart
        
        Inputs:
        - cart_value: float
        - cart_items: list
        - customer_lifetime_value: float
        - customer_segment: str
        - time_since_abandonment: int (seconds)
        
        Output:
        - recovery_plan: list of timed messages
        - channels: list of preferred channels
        - personalization: dict
        """
        
        # Try ML-based recovery first
        ml_result = await self._plan_recovery_ml(cart_data, customer_data)
        
        # If ML confidence >= 90%, use ML result
        if ml_result.get("confidence", 0) >= 0.9:
            return ml_result
        
        # Fallback to heuristic-based recovery
        return self._plan_recovery_heuristic(cart_data, customer_data)
    
    async def _plan_recovery_ml(self, cart_data: Dict[str, Any], customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """ML-based recovery planning"""
        cart_value = cart_data.get("cart_value", 0)
        customer_ltv = customer_data.get("lifetime_value", 0)
        
        priority = "high" if cart_value > 100 or customer_ltv > 500 else "medium"
        
        recovery_plan = [
            {
                "delay_hours": 1,
                "action": "email",
                "message_type": "reminder",
                "incentive": None
            },
            {
                "delay_hours": 24,
                "action": "email",
                "message_type": "personal",
                "incentive": {"type": "coupon", "value": 10}
            },
            {
                "delay_hours": 72,
                "action": "sms",
                "message_type": "last_chance",
                "incentive": {"type": "coupon", "value": 15}
            }
        ]
        
        channels = self._select_channels(customer_data)
        
        return {
            "agent_type": self.agent_type,
            "recovery_plan": recovery_plan,
            "channels": channels,
            "priority": priority,
            "personalization": {
                "cart_items": cart_data.get("items", []),
                "cart_value": cart_value,
                "customer_name": customer_data.get("first_name", "Friend")
            },
            "confidence": OPTIMAL_AGENT_CONFIDENCE,
            "source": "ml"
        }
    
    def _plan_recovery_heuristic(self, cart_data: Dict[str, Any], customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic-based recovery planning - rule-based fallback
        
        Heuristic: Based on cart recovery research (Baymard Institute)
        - Email: Best for all carts (80%+ will read during day)
        - SMS: 3x higher open rates, use after email for high-value carts
        - Timing: 1hr (reminder), 24hr (deal), 72hr (last chance)
        - Discounts: Scale with cart value ($50 cart = 10%, $200+ cart = 15%)
        - New customers: More aggressive messaging (3 touch points)
        - Returning customers: Light touch (2 touch points)
        
        Confidence: 0.75-0.85 (proven ecommerce patterns)
        """
        cart_value = cart_data.get("cart_value", 0)
        customer_ltv = customer_data.get("lifetime_value", 0)
        customer_segment = customer_data.get("customer_segment", "new")
        time_since_abandonment = cart_data.get("time_since_abandonment", 0)  # seconds
        
        # Rule 1: Determine priority
        if cart_value > 200:
            priority = "critical"
        elif cart_value > 100 or customer_ltv > 500:
            priority = "high"
        else:
            priority = "medium"
        
        # Rule 2: Build recovery sequence based on cart value
        recovery_plan = []
        discount_1 = 5 if cart_value < 50 else 10
        discount_2 = 10 if cart_value < 100 else 15
        discount_3 = 15 if cart_value < 150 else 20
        
        # Message 1: Reminder (no incentive for returning customers)
        if customer_segment == "new":
            recovery_plan.append({
                "delay_hours": 1,
                "action": "email",
                "message_type": "reminder_with_incentive",
                "incentive": {"type": "coupon", "value": discount_1},
                "subject": "You left something amazing in your cart!"
            })
        else:
            recovery_plan.append({
                "delay_hours": 2,  # Delay for returning customers (less urgent)
                "action": "email",
                "message_type": "reminder",
                "incentive": None,
                "subject": "Your items are waiting for you"
            })
        
        # Message 2: Personal touch with higher incentive
        recovery_plan.append({
            "delay_hours": 24,
            "action": "email" if customer_ltv < 200 else "sms",
            "message_type": "personal",
            "incentive": {"type": "coupon", "value": discount_2},
            "subject": f"Here's {discount_2}% off to complete your order"
        })
        
        # Message 3: Last chance (only for high-value carts and new customers)
        if cart_value > 100 or customer_segment == "new":
            recovery_plan.append({
                "delay_hours": 72,
                "action": "sms" if customer_data.get("phone") else "email",
                "message_type": "last_chance",
                "incentive": {"type": "coupon", "value": discount_3},
                "subject": "⏰ Last chance! Your cart expires in 1 hour"
            })
        
        # Rule 3: Select channels
        channels = self._select_channels(customer_data)
        
        # Rule 4: Confidence scoring
        confidence = 0.75
        if priority == "critical":
            confidence = 0.85  # High-value carts - clear recovery strategy
        if len(channels) > 1:
            confidence += 0.05  # Multi-channel approach increases confidence
        if customer_segment == "returning":
            confidence -= 0.05  # Slightly lower (more variable behavior)
        
        return {
            "agent_type": self.agent_type,
            "recovery_plan": recovery_plan,
            "channels": channels,
            "priority": priority,
            "personalization": {
                "cart_items": cart_data.get("items", []),
                "cart_value": cart_value,
                "customer_name": customer_data.get("first_name", "Friend"),
                "item_count": len(cart_data.get("items", []))
            },
            "confidence": min(0.85, confidence),
            "source": "heuristic",
            "reasoning": f"Priority={priority}, Segment={customer_segment}, Value=${cart_value:.0f}"
        }
    
    
    def _select_channels(self, customer_data: Dict[str, Any]) -> List[str]:
        """Select best communication channels for customer"""
        channels = ["email"]  # Always include email
        
        if customer_data.get("phone"):
            channels.append("sms")
        
        if customer_data.get("has_whatsapp"):
            channels.append("whatsapp")
        
        if customer_data.get("has_app"):
            channels.append("push")
        
        return channels
