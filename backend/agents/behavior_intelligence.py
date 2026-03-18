"""Behavior Intelligence Agent - Predicts purchase intent and abandonment"""
from typing import Dict, Any
import json
from backend.api.config import MIN_AGENT_CONFIDENCE


class BehaviorIntelligenceAgent:
    """
    Predicts:
    - Purchase probability (0-1)
    - Abandonment probability (0-1)
    - Intent class (high, medium, low)
    """
    
    def __init__(self, inference_client):
        self.inference_client = inference_client
        self.agent_type = "behavior_intelligence"
    
    async def predict(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make behavioral predictions based on session data
        
        Inputs:
        - page_views: int
        - product_views: int
        - scroll_depth: float (0-1)
        - time_on_site: int (seconds)
        - device: str (mobile, desktop, tablet)
        - traffic_source: str
        - recent_events: list
        
        Outputs:
        - purchase_probability: float (0-1)
        - abandonment_probability: float (0-1)
        - intent_class: str (high, medium, low)
        """
        
        # Try ML-based prediction first
        ml_result = await self._predict_ml(session_data)
        
        # If ML confidence >= 90%, use it
        if ml_result.get("confidence", 0) >= 0.9:
            return ml_result
        
        # Fallback to heuristic-based prediction
        return self._predict_heuristic(session_data)
    
    async def _predict_ml(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """ML-based behavioral prediction"""
        predictions = await self.inference_client.predict("behavior", session_data)
        
        return {
            "agent_type": self.agent_type,
            "purchase_probability": predictions.get("purchase_probability", 0),
            "abandonment_probability": predictions.get("abandonment_probability", 0),
            "intent_class": predictions.get("intent_class", "low"),
            "confidence": predictions.get("confidence", MIN_AGENT_CONFIDENCE),
            "source": "ml"
        }
    
    def _predict_heuristic(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic-based behavioral prediction - rule-based fallback
        
        Heuristic: Based on behavioral psychology research (Nielsen, Kaplan) and ecommerce studies
        Signals of purchase intent:
        - High page views (>5) + product views (>3) = exploring intent
        - High scroll depth (>0.7) = engaged with content
        - Long time on site (>2min) = seriously considering
        - Multiple product views = comparing
        - Added to cart = definite intent
        
        Signals of abandonment:
        - Quick exit (page views <2) = browse only
        - Mobile traffic + technical issues = friction
        - External traffic source = price comparison behavior
        - Late evening hours = impulse consideration
        
        Confidence: 0.70-0.80 (proven patterns)
        """
        page_views = session_data.get("page_views", 0)
        product_views = session_data.get("product_views", 0)
        scroll_depth = session_data.get("scroll_depth", 0)
        time_on_site = session_data.get("time_on_site", 0)  # seconds
        device = session_data.get("device", "desktop")
        traffic_source = session_data.get("traffic_source", "organic")
        has_cart_item = session_data.get("has_cart_item", False)
        
        # Rule 1: Baseline intent from engagement metrics
        engagement_score = 0
        engagement_score += min(page_views * 0.1, 0.3)  # Max 0.3 from page views
        engagement_score += min(product_views * 0.15, 0.4)  # Max 0.4 from product views
        engagement_score += scroll_depth * 0.2  # Max 0.2 from scroll depth
        engagement_score += min(time_on_site / 300, 0.2)  # Max 0.2 from time (5 min = max)
        
        purchase_probability = min(engagement_score, 0.95)
        
        # Rule 2: Intent class based on metrics
        if page_views < 2 or (time_on_site < 30 and page_views < 3):
            intent_class = "low"
        elif product_views >= 3 or (time_on_site > 120 and scroll_depth > 0.5):
            intent_class = "high"
        else:
            intent_class = "medium"
        
        # Rule 3: Cart presence = strong signal
        if has_cart_item:
            purchase_probability = max(purchase_probability, 0.6)
            intent_class = "high" if intent_class != "low" else "medium"
        
        # Rule 4: Abandonment risk signals
        abandonment_probability = 0
        
        # Signal A: Quick exit = low engagement
        if page_views < 2:
            abandonment_probability = 0.8
        elif page_views < 3:
            abandonment_probability = 0.5
        
        # Signal B: Mobile often has higher abandonment (friction)
        if device == "mobile":
            abandonment_probability += 0.15
        
        # Signal C: External traffic (comparison shopping)
        if traffic_source in ["google_ads", "facebook_ads", "price_comparison"]:
            abandonment_probability += 0.1
        
        # Signal D: If has cart but long engagement = reconsidering
        if has_cart_item and time_on_site > 300:
            abandonment_probability = min(0.7, abandonment_probability + 0.2)
        
        abandonment_probability = min(abandonment_probability, 0.95)
        
        # Rule 5: Inverse relationship (can't be both very high)
        if purchase_probability > 0.7:
            abandonment_probability = max(0, abandonment_probability - 0.2)
        
        # Rule 6: Confidence scoring
        confidence = 0.70
        if page_views >= 5:
            confidence += 0.05  # More data = more confident
        if product_views >= 3:
            confidence += 0.05
        if has_cart_item:
            confidence += 0.05  # Clear signal
        if page_views < 2:
            confidence += 0.05  # Clear no-purchase signal
        
        return {
            "agent_type": self.agent_type,
            "purchase_probability": round(purchase_probability, 2),
            "abandonment_probability": round(abandonment_probability, 2),
            "intent_class": intent_class,
            "confidence": min(confidence, 0.80),
            "source": "heuristic",
            "reasoning": f"Views={page_views}, Time={time_on_site}s, Device={device}, Cart={has_cart_item}"
        }
    
