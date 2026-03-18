"""Agent Orchestrator - Routes events to agents and ranks decisions"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from ..agents.behavior_intelligence import BehaviorIntelligenceAgent
from ..agents.checkout_persuasion import CheckoutPersuasionAgent
from ..agents.cart_recovery import CartRecoveryAgent
from ..agents.pricing_optimization import PricingOptimizationAgent
from ..agents.recommendation import RecommendationAgent
from ..agents.retention import RetentionAgent
from ..agents.experimentation import ExperimentationAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Central orchestrator for all agents
    
    Responsibilities:
    1. Receive events
    2. Invoke relevant agents
    3. Rank agent decisions by expected value
    4. Execute best action
    5. Record decisions and outcomes
    """
    
    def __init__(self, db, inference_client, messaging_service, shopify_service):
        self.db = db
        self.inference_client = inference_client
        self.messaging_service = messaging_service
        self.shopify_service = shopify_service
        
        # Initialize agents
        self.behavior_agent = BehaviorIntelligenceAgent(inference_client)
        self.persuasion_agent = CheckoutPersuasionAgent(inference_client)
        self.recovery_agent = CartRecoveryAgent(messaging_service, inference_client)
        self.pricing_agent = PricingOptimizationAgent(inference_client)
        self.recommendation_agent = RecommendationAgent(inference_client, shopify_service)
        self.retention_agent = RetentionAgent(inference_client)
        self.experimentation_agent = ExperimentationAgent(inference_client)
    
    async def process_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming event and determine best agent action
        
        Args:
            event: Event data from Kafka
        
        Returns:
            Best action to execute, or None if no action recommended
        """
        
        event_type = event.get("event_type")
        session_id = event.get("session_id")
        store_id = event.get("store_id")
        customer_id = event.get("customer_id")
        
        # Get session and customer data
        from ..models.models import Session as SessionModel, Customer, Cart
        
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None
        
        customer = None
        if customer_id:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        
        # Get active cart if any
        cart = self.db.query(Cart).filter(
            Cart.session_id == session_id,
            Cart.status == "active"
        ).first()
        
        # Route to appropriate agent(s) based on event type
        decisions = []
        
        if event_type == "page_view":
            # Update behavior predictions
            behavior_prediction = await self.behavior_agent.predict({
                "page_views": session.page_views,
                "product_views": session.product_views,
                "scroll_depth": session.scroll_depth,
                "time_on_site": 0,
                "device": session.device,
                "traffic_source": session.traffic_source
            })
            
            # Update session
            session.purchase_probability = behavior_prediction["purchase_probability"]
            session.abandonment_probability = behavior_prediction["abandonment_probability"]
            session.intent_class = behavior_prediction["intent_class"]
            self.db.commit()
        
        elif event_type == "add_to_cart" or (cart and cart.status == "active"):
            # Checkout persuasion agent
            if cart:
                persuasion_decision = await self.persuasion_agent.suggest_action({
                    "cart_value": cart.cart_value,
                    "product_count": cart.item_count,
                    "purchase_probability": session.purchase_probability,
                    "abandonment_probability": session.abandonment_probability
                })
                decisions.append(persuasion_decision)
            
            # Recommendation agent
            if cart and cart.items:
                recommendation_decision = await self.recommendation_agent.recommend(
                    {"cart_items": len(cart.items)},
                    cart.items
                )
                decisions.append(recommendation_decision)
        
        elif event_type == "cart_abandoned":
            # Cart recovery agent
            if cart and customer:
                recovery_decision = await self.recovery_agent.plan_recovery(
                    {
                        "cart_value": cart.cart_value,
                        "items": cart.items,
                        "time_since_abandonment": 0
                    },
                    {
                        "lifetime_value": customer.lifetime_value,
                        "first_name": customer.first_name,
                        "phone": customer.phone
                    }
                )
                decisions.append(recovery_decision)
        
        elif event_type == "order_completed":
            # Retention agent
            if customer:
                retention_decision = await self.retention_agent.plan_retention({
                    "lifetime_value": customer.lifetime_value,
                    "churn_risk": customer.churn_risk,
                    "days_since_purchase": 0,
                    "replenishment_products": []
                })
                decisions.append(retention_decision)
        
        # Rank decisions by expected value
        if decisions:
            best_decision = self._rank_decisions(decisions, session_id, store_id)
            
            # Record decision
            if best_decision:
                await self._record_decision(best_decision, session_id, store_id, customer_id)
                
                # Execute action
                await self._execute_action(best_decision, session, customer, cart)
                
                return best_decision
        
        return None
    
    def _rank_decisions(self, decisions: List[Dict], session_id: str, store_id: str) -> Optional[Dict]:
        """
        Rank decisions by expected value
        
        Formula:
        expected_value = confidence * conversion_lift * revenue_impact
        """
        
        if not decisions:
            return None
        
        # Score each decision
        scored = []
        for decision in decisions:
            confidence = decision.get("confidence", 0.5)
            # Different agents have different value functions
            agent_type = decision.get("agent_type")
            
            if agent_type == "checkout_persuasion":
                # Persuasion has immediate impact
                score = confidence * 0.85
            elif agent_type == "cart_recovery":
                # Recovery has delayed but reliable impact
                score = confidence * 0.75
            elif agent_type == "recommendation":
                # Recommendations increase AOV
                score = confidence * 0.65
            else:
                score = confidence * 0.5
            
            scored.append((score, decision))
        
        # Return highest scored decision
        best = max(scored, key=lambda x: x[0])
        return best[1]
    
    async def _record_decision(self, decision: Dict[str, Any], session_id: str, store_id: str, customer_id: Optional[str]):
        """Record agent decision in database"""
        from ..models.models import AgentAction
        import secrets
        
        action = AgentAction(
            id=f"action_{secrets.token_urlsafe(12)}",
            store_id=store_id,
            session_id=session_id,
            agent_type=decision.get("agent_type"),
            action=decision.get("action"),
            action_details=decision.get("action_details", {}),
            confidence=decision.get("confidence", 0.5),
            created_at=datetime.utcnow()
        )
        
        self.db.add(action)
        self.db.commit()
    
    async def _execute_action(self, decision: Dict[str, Any], session, customer, cart):
        """Execute the agent's recommended action"""
        
        agent_type = decision.get("agent_type")
        action = decision.get("action")
        
        # Actions are executed by specific services
        if agent_type == "checkout_persuasion":
            # Show banner/popup to user
            pass
        
        elif agent_type == "cart_recovery":
            # Schedule recovery campaign
            pass
        
        elif agent_type == "recommendation":
            # Return recommendations to frontend
            pass
        
        elif agent_type == "retention":
            # Schedule retention campaigns
            pass
        
        logger.info(f"Executed {agent_type} action: {action}")
