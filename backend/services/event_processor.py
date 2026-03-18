"""Event processing service"""
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..models.models import Event, Session as SessionModel, Customer


async def process_event(event: Dict[str, Any], db: Session):
    """
    Process an incoming event
    
    Handles:
    - Session state updates
    - Behavior tracking
    - Prediction updates
    - Agent triggering
    """
    event_type = event.get("event_type")
    session_id = event.get("session_id")
    store_id = event.get("store_id")
    
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        return
    
    # Update session based on event type
    if event_type == "page_view":
        session.page_views += 1
        session.last_activity = datetime.utcnow()
    
    elif event_type == "product_view":
        session.product_views += 1
        session.last_activity = datetime.utcnow()
    
    elif event_type == "scroll":
        scroll_depth = event.get("event_data", {}).get("scroll_depth", 0)
        session.scroll_depth = max(session.scroll_depth, scroll_depth)
    
    elif event_type == "add_to_cart":
        # May trigger checkout persuasion agent
        pass
    
    elif event_type == "page_exit":
        # May trigger cart recovery if cart is abandoned
        pass
    
    db.commit()


async def update_behavior_predictions(session_id: str, db: Session):
    """Update purchase intent and abandonment predictions"""
    from ..ml.inference_client import InferenceClient
    
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        return
    
    # Get recent events
    events = db.query(Event).filter(
        Event.session_id == session_id
    ).order_by(Event.created_at.desc()).limit(100).all()
    
    # Create features
    features = {
        "page_views": session.page_views,
        "product_views": session.product_views,
        "scroll_depth": session.scroll_depth,
        "time_on_site": (datetime.utcnow() - session.start_time).total_seconds(),
        "event_count": len(events),
        "device": session.device,
        "traffic_source": session.traffic_source
    }
    
    # Get predictions
    client = InferenceClient()
    predictions = await client.predict("behavior", features)
    
    session.purchase_probability = predictions.get("purchase_probability", 0)
    session.abandonment_probability = predictions.get("abandonment_probability", 0)
    session.intent_class = predictions.get("intent_class", "low")
    
    db.commit()
