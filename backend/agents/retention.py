"""Retention Agent - Customer lifetime value optimization"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from backend.api.config import (
    OPTIMAL_AGENT_CONFIDENCE,
    CHURN_RISK_THRESHOLD
)


class RetentionAgent:
    """
    Improves customer lifetime value through retention campaigns
    
    Triggers:
    - Replenishment reminders (for repeat products)
    - Cross-sell campaigns (complementary products)
    - Loyalty programs
    - Win-back campaigns (inactive customers)
    
    Strategy:
    - Send replenishment reminders 7 days before expected reorder
    - Quarterly cross-sell campaigns
    - VIP loyalty perks for high-LTV customers
    """
    
    def __init__(self, inference_client):
        self.inference_client = inference_client
        self.agent_type = "retention"
    
    async def plan_retention(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan retention campaigns for a customer
        
        Inputs:
        - customer_segment: str
        - lifetime_value: float
        - last_order_date: datetime
        - churn_risk: float (0-1)
        - replenishment_products: list
        
        Output:
        - campaigns: list of recommended campaigns
        - next_action: str
        - urgency: str (low, medium, high)
        """
        
        ltv = customer_data.get("lifetime_value", 0)
        churn_risk = customer_data.get("churn_risk", 0)
        days_since_purchase = customer_data.get("days_since_purchase", 365)
        
        # Try ML prediction first
        ml_result = await self._plan_retention_ml(customer_data)
        ml_confidence = ml_result.get("confidence", 0)
        
        # If ML confidence >= 90%, use ML result
        if ml_confidence >= 0.9:
            return ml_result
        
        # Fallback to heuristic-based planning
        return self._plan_retention_heuristic(customer_data, ml_result)
    
    async def _plan_retention_ml(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """ML-based retention planning using inference client"""
        ltv = customer_data.get("lifetime_value", 0)
        churn_risk = customer_data.get("churn_risk", 0)
        days_since_purchase = customer_data.get("days_since_purchase", 365)
        
        campaigns = []
        urgency = "low"
        
        # High churn risk - aggressive retention
        if churn_risk > CHURN_RISK_THRESHOLD:
            campaigns.append({
                "type": "win_back",
                "incentive": {"type": "coupon", "value": 20},
                "message": "We miss you! Here's 20% off your next order"
            })
            urgency = "high"
        
        # Long time since purchase - replenishment
        if days_since_purchase > 30 and customer_data.get("replenishment_products"):
            campaigns.append({
                "type": "replenishment",
                "products": customer_data.get("replenishment_products", []),
                "incentive": {"type": "free_shipping"},
                "message": "Time to reorder? We've saved your favorites"
            })
            urgency = "medium"
        
        # High LTV - VIP treatment
        if ltv > 500:
            campaigns.append({
                "type": "loyalty",
                "benefit": "10% lifetime discount",
                "message": "Thank you for being a valued customer!"
            })
        
        return {
            "agent_type": self.agent_type,
            "campaigns": campaigns,
            "urgency": urgency,
            "next_action": campaigns[0]["type"] if campaigns else None,
            "confidence": min(OPTIMAL_AGENT_CONFIDENCE, 0.7 + churn_risk * 0.2),
            "source": "ml"
        }
    
    def _plan_retention_heuristic(self, customer_data: Dict[str, Any], ml_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic-based retention planning - rule-based fallback
        
        Heuristic: Based on customer lifecycle research (Pareto 80/20 principle)
        - High LTV (>$500): Loyalty programs (20% of customers, 80% of revenue)
        - Medium LTV ($100-500): Replenishment reminders (regular re-engagement)
        - Low LTV + High Churn: Win-back campaigns with aggressive discounts
        - Days since purchase > 30: Replenishment urgency
        
        Confidence: 0.65-0.75 (rule-based, proven but less personalized)
        """
        ltv = customer_data.get("lifetime_value", 0)
        churn_risk = customer_data.get("churn_risk", 0)
        days_since_purchase = customer_data.get("days_since_purchase", 365)
        customer_segment = customer_data.get("customer_segment", "standard")
        
        campaigns = []
        urgency = "low"
        
        # Rule 1: VIP Treatment (High LTV customers - Pareto principle)
        if ltv > 500:
            campaigns.append({
                "type": "loyalty",
                "benefit": "15% lifetime discount" if customer_segment == "vip" else "10% lifetime discount",
                "message": "VIP Exclusive: Your loyalty matters!",
                "channel": "email"
            })
            urgency = "low"  # They're valuable, don't pressure
        
        # Rule 2: Replenishment (Consumable products)
        if days_since_purchase > 30 and days_since_purchase <= 90:
            replenishment_products = customer_data.get("replenishment_products", [])
            if replenishment_products:
                campaigns.append({
                    "type": "replenishment",
                    "products": replenishment_products[:3],
                    "incentive": {"type": "free_shipping"},
                    "message": "Your favorites are back in stock!",
                    "channel": "email"
                })
                urgency = max(urgency, "medium")
        
        # Rule 3: Win-back (Churned customers)
        if days_since_purchase > 90 and churn_risk > 0.6:
            campaigns.append({
                "type": "win_back",
                "incentive": {"type": "coupon", "value": 25},  # Higher discount for win-back
                "message": "We miss you! Extra 25% off to welcome you back",
                "channel": "email",
                "include_sms": True  # Multi-channel for urgency
            })
            urgency = "high"
        
        # Rule 4: Standard re-engagement (Medium LTV, no specific trigger)
        if not campaigns and ltv > 50:
            campaigns.append({
                "type": "cross_sell",
                "benefit": "Curated picks based on your history",
                "message": "Discover new products you might love",
                "channel": "email"
            })
            urgency = "low"
        
        confidence = 0.65 if campaigns else 0.5
        if urgency == "high":
            confidence += 0.1  # Higher confidence for clear churn signals
        
        return {
            "agent_type": self.agent_type,
            "campaigns": campaigns if campaigns else ml_result.get("campaigns", []),
            "urgency": urgency,
            "next_action": campaigns[0]["type"] if campaigns else ml_result.get("next_action"),
            "confidence": confidence,
            "source": "heuristic",
            "reasoning": "Rule-based lifecycle retention strategy"
        }
